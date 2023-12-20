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
            if chan.is_hotspot():
                locators_to_channels["Hotspot"] += [chan.internal_id]
                continue

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
                prefix_to_channels[prefix] += [chan.internal_id]

        for key in sorted(prefix_to_channels.keys()):
            value = sorted(prefix_to_channels[key])
            yield Zone(internal_id=seq.next(), name=key, channels=value)
