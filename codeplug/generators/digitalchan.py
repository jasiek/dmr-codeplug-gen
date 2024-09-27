import json

import maidenhead as mh

from models import DigitalChannel, AnalogChannel, TxPower, ChannelWidth
from datasources import brandmeister


def channel_label(callsign, tg):
    return f"{tg.calling_id} {tg.name}"


def hotspot_channel_label(contact):
    return f"HS{contact.calling_id} {contact.name}"


class HotspotDigitalChannelGenerator:
    def __init__(self, talkgroups, *, aprs_config, ts=2, f=438.800, color=1):
        self.f = f
        self.ts = ts
        self.color = color
        self.talkgroups = talkgroups
        self._channels = []
        self.aprs_config = aprs_config

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
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    color=self.color,
                    slot=slot,
                    rx_grouplist_id="-",
                    tx_contact_id=None,
                    aprs=self.aprs_config,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )

        for tg in self.talkgroups:
            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=hotspot_channel_label(tg),
                    rx_freq=self.f,
                    tx_freq=self.f,
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    color=self.color,
                    slot=self.ts,
                    rx_grouplist_id="-",
                    tx_contact_id=tg.internal_id,
                    aprs=self.aprs_config,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )


class DigitalChannelGeneratorFromBrandmeister:
    def __init__(self, power, talkgroups, *, aprs_config):
        self.devices = brandmeister.DeviceDB().devices_active_within1month()
        self._channels = []
        self.talkgroups = talkgroups
        self.aprs_config = aprs_config

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

                        name = channel_label(dev["callsign"], tg)
                        self._channels.append(
                            DigitalChannel(
                                internal_id=sequence.next(),
                                name=name,
                                rx_freq=float(dev["tx"]),
                                tx_freq=float(dev["rx"]),
                                tx_power=TxPower.High,
                                scanlist_id="-",
                                tot=None,
                                rx_only=False,
                                admit_crit="Free",
                                color=dev["colorcode"],
                                slot=slot,
                                rx_grouplist_id="-",
                                tx_contact_id=str(tg.internal_id),
                                aprs=self.aprs_config,
                                _lat=float(dev["lat"]),
                                _lng=float(dev["lng"]),
                                _locator=mh.to_maiden(dev["lat"], dev["lng"], 3),
                                _rpt_callsign=dev["callsign"],
                                _qth=dev["city"],
                            )
                        )

            for slot in [1, 2]:
                name = " ".join(
                    [
                        dev["callsign"],
                        f"TS{slot}",
                    ]
                )

                self._channels.append(
                    DigitalChannel(
                        internal_id=sequence.next(),
                        name=name,
                        rx_freq=float(dev["tx"]),
                        tx_freq=float(dev["rx"]),
                        tx_power=TxPower.High,
                        scanlist_id="-",
                        tot=None,
                        rx_only=False,
                        admit_crit="Free",
                        color=dev["colorcode"],
                        slot=slot,
                        rx_grouplist_id="-",
                        tx_contact_id=None,
                        aprs=self.aprs_config,
                        _lat=float(dev["lat"]),
                        _lng=float(dev["lng"]),
                        _locator=mh.to_maiden(dev["lat"], dev["lng"], 3),
                        _rpt_callsign=dev["callsign"],
                        _qth=dev["city"],
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
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    color=int(64 * (chan_freq % 0.4)),  # per TS 102 658
                    slot=2,
                    rx_grouplist_id="-",
                    tx_contact_id=None,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )
        return self._channels
