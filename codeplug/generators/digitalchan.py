import json

import maidenhead as mh

from models import DigitalChannel, AnalogChannel, TxPower, ChannelWidth
from datasources import brandmeister


def format_channel(s):
    return s


class HotspotDigitalChannelGenerator:
    def __init__(self, talkgroups, ts=2, f=438.800, color=1):
        self.f = f
        self.ts = ts
        self.color = color
        self.talkgroups = talkgroups
        self._channels = []

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for slot in [1, 2]:
            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=f"HS TS{slot}",
                    rx_freq=self.f,
                    tx_freq=self.f,
                    tx_power=TxPower.Min,
                    scanlist_id="-",
                    tot="-",
                    rx_only="-",
                    admit_crit="Free",
                    color=self.color,
                    slot=slot,
                    rx_grouplist_id="-",
                    tx_contact_id=None,
                    lat=None,
                    lng=None,
                    locator=None,
                )
            )

        for tg in self.talkgroups:
            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=format_channel(f"HS {tg.calling_id} {tg.name}"),
                    rx_freq=self.f,
                    tx_freq=self.f,
                    tx_power=TxPower.Min,
                    scanlist_id="-",
                    tot="-",
                    rx_only="-",
                    admit_crit="Free",
                    color=self.color,
                    slot=self.ts,
                    rx_grouplist_id="-",
                    tx_contact_id=tg.internal_id,
                    lat=None,
                    lng=None,
                    locator=None,
                )
            )


class DigitalChannelGeneratorFromBrandmeister:
    def __init__(self, power, talkgroups):
        self.devices = brandmeister.DeviceDB().devices_active_within1month()
        self._channels = []
        self.talkgroups = talkgroups

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for dev in self.devices:
            if not dev["callsign"].startswith("SR"):
                continue

            if dev["rx"] == dev["tx"] or dev["pep"] == 1 or dev["statusText"] == "DMO":
                # Hotspot
                continue

            for tg_id, slot in brandmeister.TalkgroupAPI().static_talkgroups(dev["id"]):
                if slot == 0:
                    continue
                for tg in self.talkgroups:
                    if tg.calling_id == tg_id:
                        # We were passed a TG definition

                        name = format_channel(
                            " ".join([dev["callsign"], str(tg.calling_id)])
                        )
                        self._channels.append(
                            DigitalChannel(
                                internal_id=sequence.next(),
                                name=name,
                                rx_freq=float(dev["tx"]),
                                tx_freq=float(dev["rx"]),
                                tx_power=TxPower.High,
                                scanlist_id="-",
                                tot="-",
                                rx_only="-",
                                admit_crit="Free",
                                color=dev["colorcode"],
                                slot=slot,
                                rx_grouplist_id="-",
                                tx_contact_id=str(tg.internal_id),
                                lat=float(dev["lat"]),
                                lng=float(dev["lng"]),
                                locator=mh.to_maiden(dev["lat"], dev["lng"], 3),
                            )
                        )

            for slot in [1, 2]:
                name = format_channel(
                    " ".join(
                        [
                            dev["callsign"],
                            f"TS{slot}",
                        ]
                    )
                )

                self._channels.append(
                    DigitalChannel(
                        internal_id=sequence.next(),
                        name=name,
                        rx_freq=float(dev["tx"]),
                        tx_freq=float(dev["rx"]),
                        tx_power=TxPower.High,
                        scanlist_id="-",
                        tot="-",
                        rx_only="-",
                        admit_crit="Free",
                        color=dev["colorcode"],
                        slot=slot,
                        rx_grouplist_id="-",
                        tx_contact_id=None,
                        lat=float(dev["lat"]),
                        lng=float(dev["lng"]),
                        locator=mh.to_maiden(dev["lat"], dev["lng"], 3),
                    )
                )


class DigitalPMR446ChannelGenerator:
    def __init__(self):
        self._channels = []

    def channels(self, seq):
        f = 446.003125
        for channum in range(1, 33):
            chan_freq = f + (channum - 1) * 0.00625
            name = f"dPMR {channum}"
            self._channels.append(
                DigitalChannel(
                    internal_id=seq.next(),
                    name=name,
                    rx_freq=chan_freq,
                    tx_freq=chan_freq,
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot="-",
                    rx_only="-",
                    admit_crit="Free",
                    color=int(64 * (chan_freq % 0.4)),  # per TS 102 658
                    slot=2,
                    rx_grouplist_id="-",
                    tx_contact_id=None,
                    lat=None,
                    lng=None,
                    locator=None,
                )
            )
        return self._channels
