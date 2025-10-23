class ContactAggregator:
    def __init__(self, *contact_generators):
        self.generators = contact_generators

    def contacts(self, sequence):
        contacts = []
        for gen in self.generators:
            contacts += gen.contacts(sequence)
        return contacts


class ChannelAggregator:
    def __init__(self, *chan_generators):
        self.generators = chan_generators

    def channels(self, sequence):
        channels = []
        for gen in self.generators:
            generated_channels = gen.channels(sequence)
            if len(generated_channels) == 0:
                print(
                    f"Warning: Channel generator {gen.__class__.__name__} produced no channels."
                )
            channels += generated_channels
        return channels


class ZoneAggregator:
    def __init__(self, *zone_generators):
        self.generators = zone_generators

    def zones(self, sequence):
        zones = []
        for gen in self.generators:
            zones += gen.zones(sequence)
        return zones
