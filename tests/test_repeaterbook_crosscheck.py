import os
import sys

from lxml import etree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codeplug"))

from generators.digitalchan import (  # noqa: E402
    DigitalChannelGeneratorFromBrandmeister,
)


def device(id, callsign, tx, rx, **extra):
    return {
        "id": id,
        "callsign": callsign,
        "tx": tx,
        "rx": rx,
        "colorcode": 1,
        "pep": 0,
        "lat": 8.5,
        "lng": -80.3,
        "city": "Somewhere",
        "last_seen": "2026-10-01 00:00:00",
        **extra,
    }


def rxf(*repeaters):
    nodes = "".join(
        f"<repeater><qra>{call}</qra><mode>{mode}</mode>"
        f'<qrg type="rx">{out}</qrg><qrg type="tx">{inp}</qrg>'
        f"<qth>Staten Island, New York, Richmond</qth>"
        f"<location><latitude>40.61</latitude><longitude>-74.06</longitude></location>"
        f"</repeater>"
        for call, mode, out, inp in repeaters
    )
    return etree.fromstring(f"<rxf><repeaters>{nodes}</repeaters></rxf>")


class FakeDeviceDB:
    def __init__(self, by_call):
        self.by_call = by_call

    def devices_by_callsign(self, callsign):
        return self.by_call.get(callsign, [])


def generator(repeaterbook, by_call):
    gen = object.__new__(DigitalChannelGeneratorFromBrandmeister)
    gen.repeaterbook = repeaterbook
    gen.device_db = FakeDeviceDB(by_call)
    gen.debug = False
    return gen


class TestRepeaterBookDevices:
    def test_hotspot_registration_gets_repeaterbook_data(self):
        hotspot = device(1, "W2CSW", "147.0000", "147.0000", pep=1)
        gen = generator(
            rxf(("W2CSW", "dmr", "446.62500", "441.62500")), {"W2CSW": [hotspot]}
        )

        [dev] = gen.repeaterbook_devices([])

        assert dev["id"] == 1
        assert dev["tx"] == 446.625
        assert dev["rx"] == 441.625
        assert (dev["lat"], dev["lng"]) == (40.61, -74.06)
        assert dev["city"] == "Staten Island"

    def test_skips_repeater_already_listed(self):
        listed = device(1, "W2XYZ Somewhere", "446.6250", "441.6250")
        gen = generator(rxf(("W2XYZ", "dmr", "446.62500", "441.62500")), {})

        assert gen.repeaterbook_devices([listed]) == []

    def test_prefers_frequency_match(self):
        devices = [
            device(1, "W2XYZ", "444.5250", "444.5250", last_seen="2026-10-12"),
            device(2, "W2XYZ", "446.6250", "441.6250", last_seen="2026-01-01"),
        ]
        gen = generator(
            rxf(("W2XYZ", "dmr", "446.62500", "441.62500")), {"W2XYZ": devices}
        )

        [dev] = gen.repeaterbook_devices([])

        assert dev["id"] == 2

    def test_no_guess_when_callsign_already_listed(self):
        listed = device(1, "W2XYZ", "440.3000", "445.3000")
        other = device(2, "W2XYZ", "444.5250", "444.5250")
        gen = generator(
            rxf(("W2XYZ", "dmr", "146.65500", "146.05500")),
            {"W2XYZ": [listed, other]},
        )

        assert gen.repeaterbook_devices([listed]) == []

    def test_ignores_non_dmr_and_unknown_callsigns(self):
        gen = generator(
            rxf(
                ("W2FM", "fm", "146.62500", "146.02500"),
                ("W2NONE", "dmr", "446.62500", "441.62500"),
            ),
            {"W2FM": [device(1, "W2FM", "0", "0")]},
        )

        assert gen.repeaterbook_devices([]) == []
