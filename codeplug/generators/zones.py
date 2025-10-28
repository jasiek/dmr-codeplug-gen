import re
from collections import defaultdict

from generators import Sequence
from models import Zone, DigitalChannel, is_hotspot, AnalogChannel


class ZoneFromLocatorGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        locators_to_channels = defaultdict(lambda: [])
        for chan in self.channels:
            if chan.locator is None:
                continue

            locator = chan.locator[0:4]
            if isinstance(chan, DigitalChannel):
                locator_label = f"Digital {locator}"
            else:
                locator_label = f"Analog {locator}"

            if chan.locator == "":
                locators_to_channels["No locator"] += [chan]
            else:
                locators_to_channels[locator_label] += [chan]

        for key in sorted(locators_to_channels.keys()):
            channels = sorted(locators_to_channels[key], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]
            yield Zone(internal_id=seq.next(), name=key, channels=channel_ids)


class ZoneFromCallsignGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        prefix_to_channels = defaultdict(lambda: [])
        for chan in self.channels:
            if m := re.match("^([A-Z]{2}[0-9])", chan._rpt_callsign):
                prefix = m.groups()[0]
                if isinstance(chan, DigitalChannel):
                    label = f"{prefix} Digital"
                else:
                    label = f"{prefix} Analog"
                prefix_to_channels[label] += [chan]

        output = []
        for key in sorted(prefix_to_channels.keys()):
            channels = sorted(prefix_to_channels[key], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]
            output.append(Zone(internal_id=seq.next(), name=key, channels=channel_ids))
        return output


class ZoneFromCallsignGenerator2:
    # NOTE: 26/12/2023 (jps): Per-callsign clustering of channels
    def __init__(self, channels, with_qth=True):
        self.channels = channels
        self.with_qth = with_qth

    def zones(self, seq):
        callsign_to_channels = defaultdict(lambda: [])
        for chan in self.channels:
            callsign_to_channels[chan._rpt_callsign].append(chan)

        output = []

        del callsign_to_channels[None]  # ignore hotspots

        for key in sorted(callsign_to_channels.keys()):
            channels = sorted(callsign_to_channels[key], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]
            if self.with_qth:
                name = f"{key} {channels[0]._qth}"
            else:
                name = key
            output.append(Zone(internal_id=seq.next(), name=name, channels=channel_ids))
        return output


class PMRZoneGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        return [
            Zone(
                internal_id=seq.next(),
                name="PMR",
                channels=[ch.internal_id for ch in self.channels],
            )
        ]


class AnalogZoneGenerator:
    def __init__(self, channels, zone_name="Analog"):
        self.channels = channels
        self.zone_name = zone_name

    def zones(self, seq):
        analog_channels = []
        for chan in self.channels:
            if isinstance(chan, AnalogChannel):
                analog_channels.append(chan.internal_id)

        if len(analog_channels) == 0:
            print(f"No analog channels found, skipping zone '{self.zone_name}'.")
            return []

        if len(analog_channels) > 250:
            print(
                f"Too many analog channels for zone ({len(analog_channels)}) '{self.zone_name}', truncating to 250."
            )
            analog_channels = analog_channels[:250]

        return [
            Zone(internal_id=seq.next(), name=self.zone_name, channels=analog_channels),
        ]


class HotspotZoneGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        hotspot_channels = []
        for chan in self.channels:
            if is_hotspot(chan):
                hotspot_channels.append(chan.internal_id)

        return [Zone(internal_id=seq.next(), name="Hotspot", channels=hotspot_channels)]
