import re
from collections import defaultdict

from generators import Sequence
from models import Zone, DigitalChannel


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
                locators_to_channels["No locator"] += [chan.internal_id]
            else:
                locators_to_channels[locator_label] += [chan.internal_id]

        for key in sorted(locators_to_channels.keys()):
            value = sorted(locators_to_channels[key])
            yield Zone(internal_id=seq.next(), name=key, channels=value)


class ZoneFromCallsignGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        prefix_to_channels = defaultdict(lambda: [])
        for chan in self.channels:
            if m := re.match("^([A-Z]{2}[0-9])", chan.name):
                prefix = m.groups()[0]
                if isinstance(chan, DigitalChannel):
                    label = f"{prefix} Digital"
                else:
                    label = f"{prefix} Analog"
                prefix_to_channels[label] += [chan.internal_id]

        output = []
        for key in sorted(prefix_to_channels.keys()):
            value = sorted(prefix_to_channels[key])
            output.append(Zone(internal_id=seq.next(), name=key, channels=value))
        return output


class HotspotZoneGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        hotspot_channels = []
        for chan in self.channels:
            if chan.is_hotspot():
                hotspot_channels.append(chan.internal_id)

        return [Zone(internal_id=seq.next(), name="Hotspot", channels=hotspot_channels)]
