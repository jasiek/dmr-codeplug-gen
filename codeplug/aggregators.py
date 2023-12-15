class ChannelAggregator:
    def __init__(self, *chan_generators):
        self.generators = chan_generators

    def channels(self, sequence):
        for gen in self.generators:
            for chan in gen.channels(sequence):
                yield chan


class ZoneAggregator:
    def __init__(self, *zone_generators):
        self.generators = zone_generators

    def zones(self, sequence):
        for gen in self.generators:
            for zone in gen.zones():
                yield chan
