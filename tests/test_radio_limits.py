import io
from dataclasses import replace

import pytest

from codeplug.models import (
    AnalogAdmitCriteria,
    AnalogAPRSConfig,
    AnalogChannel,
    ChannelWidth,
    Contact,
    ContactType,
    DigitalAdmitCriteria,
    DigitalAPRSConfig,
    DigitalChannel,
    DigitalRoamingChannel,
    DigitalRoamingZone,
    GroupList,
    ScanList,
    TxPower,
    Zone,
)
from codeplug.radio_limits import RADIOS, CodeplugTrimmer, get_limits


def contact(i):
    return Contact(i, f"TG{i}", ContactType.GroupCall, 1000 + i)


def analog(i, scanlist_id=None, aprs=None):
    return AnalogChannel(
        i, f"A{i}", 145.0, 145.6, TxPower.High, scanlist_id, None, False,
        AnalogAdmitCriteria.Always, 1, None, None, ChannelWidth.Wide, aprs,
        None, None, None, None, None,
    )  # fmt: skip


def digital(i, contact_id=None, grouplist_id=None, scanlist_id=None):
    return DigitalChannel(
        i, f"D{i}", 439.0, 431.4, TxPower.High, scanlist_id, None, False,
        DigitalAdmitCriteria.ColorCode, 1, 1, grouplist_id, contact_id, None,
        None, None, None, None, None, None,
    )  # fmt: skip


def roaming_channel(i):
    return DigitalRoamingChannel(i, f"R{i}", 431.4, 439.0, 1, 1)


def trim(limits, **kwargs):
    sections = dict(
        contacts=[],
        grouplists=[],
        analog_channels=[],
        digital_channels=[],
        zones=[],
        scanlists=[],
        roaming_channels=[],
        roaming_zones=[],
        analog_aprs_config=None,
        digital_aprs_config=None,
    )
    sections.update(kwargs)
    out = io.StringIO()
    result = CodeplugTrimmer(limits, out=out).trim(**sections)
    return result, out.getvalue()


def small(**overrides):
    return replace(get_limits("d878uv"), **overrides)


def test_get_limits_is_case_insensitive():
    assert get_limits("D878UV") is RADIOS["d878uv"]


def test_get_limits_rejects_unknown_radio():
    with pytest.raises(ValueError, match="Supported"):
        get_limits("gd77")


def test_nothing_trimmed_when_within_limits():
    channels = [analog(i) for i in range(1, 4)]
    zones = [Zone(1, "Z", [1, 2, 3])]
    result, report = trim(small(), analog_channels=channels, zones=zones)
    assert result["analog_channels"] == channels
    assert result["zones"] == zones
    assert report == ""


def test_channel_cap_keeps_zone_order_and_aprs_channel():
    aprs = AnalogAPRSConfig(1, "APRS", 9, "SRC", "APAT81", [], "Jogger", 300, "")
    channels = [analog(i) for i in range(1, 10)]
    # Zone lists channel 8 then 5; the APRS channel 9 must survive too.
    zones = [Zone(1, "Z", [8, 5])]
    result, report = trim(
        small(channels=3),
        analog_channels=channels,
        zones=zones,
        analog_aprs_config=aprs,
    )
    kept = {ch.internal_id for ch in result["analog_channels"]}
    assert kept == {9, 8, 5}
    assert "channels: kept 3 of 9" in report


def test_zones_drop_trimmed_channels_and_empty_zones():
    channels = [analog(i) for i in range(1, 5)]
    zones = [Zone(1, "A", [1, 2]), Zone(2, "B", [3, 4])]
    result, _ = trim(small(channels=2), analog_channels=channels, zones=zones)
    assert [z.name for z in result["zones"]] == ["A"]


def test_zone_and_scanlist_member_caps():
    channels = [analog(i) for i in range(1, 6)]
    zones = [Zone(1, "Z", [1, 2, 3, 4, 5])]
    scanlists = [ScanList(1, "S", [1, 2, 3, 4, 5])]
    result, _ = trim(
        small(zone_channels=2, scanlist_channels=3),
        analog_channels=channels,
        zones=zones,
        scanlists=scanlists,
    )
    assert result["zones"][0].channels == [1, 2]
    assert result["scanlists"][0].channels == [1, 2, 3]
    # The input is not mutated
    assert zones[0].channels == [1, 2, 3, 4, 5]


def test_channel_references_to_dropped_lists_are_cleared():
    contacts = [contact(i) for i in range(1, 4)]
    grouplists = [GroupList(1, "G1", [1]), GroupList(2, "G2", [2])]
    scanlists = [ScanList(1, "S1", [10]), ScanList(2, "S2", [11])]
    chans = [
        digital(10, contact_id=1, grouplist_id=1, scanlist_id=1),
        digital(11, contact_id=2, grouplist_id=2, scanlist_id=2),
    ]
    result, _ = trim(
        small(grouplists=1, scanlists=1),
        contacts=contacts,
        grouplists=grouplists,
        scanlists=scanlists,
        digital_channels=chans,
    )
    first, second = result["digital_channels"]
    assert (first.rx_grouplist_id, first.scanlist_id) == (1, 1)
    assert (second.rx_grouplist_id, second.scanlist_id) == (None, None)
    assert second.tx_contact_id == 2


def test_contact_cap_keeps_referenced_contacts():
    contacts = [contact(i) for i in range(1, 11)]
    aprs = DigitalAPRSConfig(1, "DMR APRS", 300, 10)
    chans = [digital(100, contact_id=7)]
    grouplists = [GroupList(1, "G", [3])]
    result, report = trim(
        small(contacts=4),
        contacts=contacts,
        digital_channels=chans,
        grouplists=grouplists,
        digital_aprs_config=aprs,
    )
    # Referenced (10, 7, 3) first, then the first unreferenced one, in input order.
    assert [c.internal_id for c in result["contacts"]] == [1, 3, 7, 10]
    assert "contacts: kept 4 of 10" in report


def test_grouplist_contact_cap():
    contacts = [contact(i) for i in range(1, 6)]
    grouplists = [GroupList(1, "G", [1, 2, 3, 4, 5])]
    result, _ = trim(
        small(grouplist_contacts=2), contacts=contacts, grouplists=grouplists
    )
    assert result["grouplists"][0].contact_ids == [1, 2]


def test_roaming_caps_and_dangling_references():
    rchans = [roaming_channel(i) for i in range(1, 6)]
    rzones = [DigitalRoamingZone(1, "A", [1, 2, 3]), DigitalRoamingZone(2, "B", [4, 5])]
    result, _ = trim(
        small(roaming_channels=3, roaming_zone_channels=2),
        roaming_channels=rchans,
        roaming_zones=rzones,
    )
    assert [ch.internal_id for ch in result["roaming_channels"]] == [1, 2, 3]
    assert [(z.name, z.channels) for z in result["roaming_zones"]] == [("A", [1, 2])]
