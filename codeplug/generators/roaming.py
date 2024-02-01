import re
from collections import defaultdict

from models import DigitalRoamingChannel, DigitalRoamingZone
from datasources import brandmeister


class RoamingChannelGeneratorFromBrandmeister:
    def __init__(self, talkgroups):
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

            generated = set()
            for _, slot in brandmeister.TalkgroupAPI().static_talkgroups(dev["id"]):
                if slot == 0:
                    continue
                channel_name = f'{dev["callsign"]} TS{slot}'
                if channel_name in generated:
                    continue
                self._channels.append(
                    DigitalRoamingChannel(
                        internal_id=sequence.next(),
                        name=channel_name,
                        tx_freq=float(dev["tx"]),
                        rx_freq=float(dev["rx"]),
                        color=dev["colorcode"],
                        slot=slot,
                    )
                )
                generated.add(channel_name)


class RoamingZoneFromCallsignGenerator:
    def __init__(self, channels):
        self._channels = channels

    def zones(self, sequence):
        prefix_to_channels = defaultdict(lambda: [])
        for chan in self._channels:
            if m := re.match("^([A-Z]{2}[0-9])", chan.name):
                prefix = m.groups()[0]
                prefix_to_channels[prefix] += [chan.internal_id]

        output = []
        for key in sorted(prefix_to_channels.keys()):
            value = sorted(prefix_to_channels[key])
            output.append(
                DigitalRoamingZone(
                    internal_id=sequence.next(), name=key, channels=value
                )
            )
        return output
