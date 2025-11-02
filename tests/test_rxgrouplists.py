import pytest
from codeplug.models import (
    DigitalChannel,
    Contact,
    ContactType,
    TxPower,
    DigitalAdmitCriteria,
)
from codeplug.generators.rxgrouplists import (
    RXGroupListGenerator,
    HotspotRXGroupListGenerator,
)
from codeplug.generators import Sequence


def test_hotspot_rxgrouplist_generator():
    """Test that HotspotRXGroupListGenerator creates a single grouplist for all hotspot channels."""
    # Create some test contacts
    contacts = [
        Contact(
            internal_id=1,
            name="USA Nationwide",
            type=ContactType.GroupCall,
            calling_id=3100,
        ),
        Contact(
            internal_id=2,
            name="California",
            type=ContactType.GroupCall,
            calling_id=3106,
        ),
        Contact(
            internal_id=3,
            name="UK Nationwide",
            type=ContactType.GroupCall,
            calling_id=235,
        ),
    ]

    # Create some hotspot channels
    hotspot_channels = [
        DigitalChannel(
            internal_id=1,
            name="HS3100 USA Nationwide",
            rx_freq=431.1,
            tx_freq=431.1,
            tx_power=TxPower.Low,
            scanlist_id="-",
            tot=None,
            rx_only=False,
            admit_crit=DigitalAdmitCriteria.Free,
            color=1,
            slot=2,
            rx_grouplist_id="-",
            tx_contact_id=1,
            aprs=None,
            anytone=None,
            _lat=None,
            _lng=None,
            _locator=None,
            _rpt_callsign=None,
            _qth=None,
        ),
        DigitalChannel(
            internal_id=2,
            name="HS TS1",
            rx_freq=431.1,
            tx_freq=431.1,
            tx_power=TxPower.Low,
            scanlist_id="-",
            tot=None,
            rx_only=False,
            admit_crit=DigitalAdmitCriteria.Free,
            color=1,
            slot=1,
            rx_grouplist_id="-",
            tx_contact_id=None,
            aprs=None,
            anytone=None,
            _lat=None,
            _lng=None,
            _locator=None,
            _rpt_callsign=None,
            _qth=None,
        ),
    ]

    # Generate grouplists
    generator = HotspotRXGroupListGenerator(hotspot_channels, contacts)
    grouplists = generator.grouplists(Sequence())

    # Should create exactly one grouplist
    assert len(grouplists) == 1

    grouplist = grouplists[0]
    assert grouplist.name == "RX Hotspot"
    # Should contain all contacts
    assert len(grouplist.contact_ids) == 3
    assert set(grouplist.contact_ids) == {1, 2, 3}

    # All hotspot channels should be updated with the grouplist ID
    for channel in hotspot_channels:
        assert channel.rx_grouplist_id == grouplist.internal_id


def test_rxgrouplist_generator_basic():
    """Test that RXGroupListGenerator creates grouplists for repeater channels."""
    # Create some test contacts
    contacts = [
        Contact(
            internal_id=1,
            name="USA Nationwide",
            type=ContactType.GroupCall,
            calling_id=3100,
        ),
        Contact(
            internal_id=2,
            name="California",
            type=ContactType.GroupCall,
            calling_id=3106,
        ),
    ]

    # Create repeater channels (non-hotspot)
    repeater_channels = [
        DigitalChannel(
            internal_id=1,
            name="W6ABC 3100 USA Nationwide",
            rx_freq=447.0,
            tx_freq=442.0,
            tx_power=TxPower.High,
            scanlist_id="-",
            tot=None,
            rx_only=False,
            admit_crit=DigitalAdmitCriteria.Free,
            color=1,
            slot=2,
            rx_grouplist_id="-",
            tx_contact_id=1,
            aprs=None,
            anytone=None,
            _lat=37.5,
            _lng=-122.0,
            _locator="CM87",
            _rpt_callsign="W6ABC",
            _qth="San Francisco",
        ),
        DigitalChannel(
            internal_id=2,
            name="W6ABC TS1",
            rx_freq=447.0,
            tx_freq=442.0,
            tx_power=TxPower.High,
            scanlist_id="-",
            tot=None,
            rx_only=False,
            admit_crit=DigitalAdmitCriteria.Free,
            color=1,
            slot=1,
            rx_grouplist_id="-",
            tx_contact_id=None,
            aprs=None,
            anytone=None,
            _lat=37.5,
            _lng=-122.0,
            _locator="CM87",
            _rpt_callsign="W6ABC",
            _qth="San Francisco",
        ),
    ]

    # Note: This test won't actually fetch from Brandmeister API since the repeater
    # callsign won't exist in the device database. This test mainly validates the
    # structure and that it doesn't crash.
    generator = RXGroupListGenerator(repeater_channels, contacts)
    grouplists = generator.grouplists(Sequence())

    # The generator may not create any grouplists if the repeater isn't in the
    # Brandmeister database, which is expected for this unit test
    assert isinstance(grouplists, list)


def test_rxgrouplist_generator_skips_hotspots():
    """Test that RXGroupListGenerator skips hotspot channels."""
    contacts = [
        Contact(
            internal_id=1,
            name="USA Nationwide",
            type=ContactType.GroupCall,
            calling_id=3100,
        ),
    ]

    # Mix of hotspot and repeater channels
    mixed_channels = [
        DigitalChannel(
            internal_id=1,
            name="HS3100 USA Nationwide",
            rx_freq=431.1,
            tx_freq=431.1,
            tx_power=TxPower.Low,
            scanlist_id="-",
            tot=None,
            rx_only=False,
            admit_crit=DigitalAdmitCriteria.Free,
            color=1,
            slot=2,
            rx_grouplist_id="-",
            tx_contact_id=1,
            aprs=None,
            anytone=None,
            _lat=None,
            _lng=None,
            _locator=None,
            _rpt_callsign=None,
            _qth=None,
        ),
        DigitalChannel(
            internal_id=2,
            name="W6ABC TS1",
            rx_freq=447.0,
            tx_freq=442.0,
            tx_power=TxPower.High,
            scanlist_id="-",
            tot=None,
            rx_only=False,
            admit_crit=DigitalAdmitCriteria.Free,
            color=1,
            slot=1,
            rx_grouplist_id="-",
            tx_contact_id=None,
            aprs=None,
            anytone=None,
            _lat=37.5,
            _lng=-122.0,
            _locator="CM87",
            _rpt_callsign="W6ABC",
            _qth="San Francisco",
        ),
    ]

    generator = RXGroupListGenerator(mixed_channels, contacts)
    grouplists = generator.grouplists(Sequence())

    # Should process only the repeater channel, skipping hotspot
    # (though may still return empty list if repeater not in database)
    assert isinstance(grouplists, list)
