from collections import defaultdict

from generators import Sequence
from models import Zone, DigitalChannel


class ZoneFromLocatorGenerator:
    def __init__(self, *chan_gens):
        self.chan_gens = chan_gens
        self.locators_to_channels = defaultdict(lambda: [])

    def zones(self):
        s = Sequence()
        for chan_gen in self.chan_gens:
            for chan in chan_gen.channels(s):
                if chan.is_hotspot():
                    self.locators_to_channels["Hotspot"] += [chan.internal_id]
                    continue

                if chan.locator is None:
                    continue

                locator = chan.locator[0:4]
                if isinstance(chan, DigitalChannel):
                    locator_label = f"Digital {locator}"
                else:
                    locator_label = f"Analog {locator}"

                if chan.locator == "":
                    self.locators_to_channels["No locator"] += [chan.internal_id]
                else:
                    self.locators_to_channels[locator_label] += [chan.internal_id]

        zs = Sequence()
        for key in sorted(self.locators_to_channels.keys()):
            value = sorted(self.locators_to_channels[key])
            yield Zone(internal_id=zs.next(), name=key, channels=value)
