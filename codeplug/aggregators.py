class ChannelAggregator:
    def __init__(self, *chan_generators):
        self.generators = chan_generators

    def channels(self, sequence):
        channels = []
        for gen in self.generators:
            channels += gen.channels(sequence)
        return channels


class ZoneAggregator:
    def __init__(self, *zone_generators):
        self.generators = zone_generators

    def zones(self, sequence):
        zones = []
        for gen in self.generators:
            zones += gen.zones()
        return zones
