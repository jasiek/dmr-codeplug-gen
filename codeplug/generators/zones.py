from collections import defaultdict

from generators import Sequence
from models import Zone


class ZoneFromLocatorGenerator:
    def __init__(self, *chan_gens):
        self.chan_gens = chan_gens
        self.locators_to_channels = defaultdict(lambda: [])

    def zones(self):
        s = Sequence()
        for chan_gen in self.chan_gens:
            for chan in chan_gen.channels(s):
                if chan.locator is None or chan.locator == "":
                    continue
                locator = chan.locator[0:4]
                self.locators_to_channels[locator] += [chan.internal_id]

        zs = Sequence()
        for key in self.locators_to_channels.keys():
            value = sorted(self.locators_to_channels[key])
            yield Zone(internal_id=zs.next(), name=key, channels=value)
