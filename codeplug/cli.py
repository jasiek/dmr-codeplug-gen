import sys

from codeplug import Codeplug

from generators import Sequence
from generators.grouplists import CountryGroupListGenerator
from generators.contacts import BrandmeisterTGContactGenerator
from generators.channels import (
    AnalogChannelGeneratorFromPrzemienniki,
    DigitalChannelGeneratorFromBrandmeister,
    HotspotDigitalChannelGenerator,
)
from generators.zones import ZoneFromCallsignGenerator, HotspotZoneGenerator
from aggregators import ChannelAggregator, ZoneAggregator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("missing output file name")
        exit(1)

    contact_gen = BrandmeisterTGContactGenerator()
    polish_tgs = contact_gen.matched_contacts("^260")
    chan_seq = Sequence()
    digital_channels = ChannelAggregator(
        HotspotDigitalChannelGenerator(polish_tgs),
        DigitalChannelGeneratorFromBrandmeister("High", polish_tgs),
    ).channels(chan_seq)
    analog_channels = ChannelAggregator(
        AnalogChannelGeneratorFromPrzemienniki("data/pl_2m_fm.xml", "High"),
        AnalogChannelGeneratorFromPrzemienniki("data/pl_70cm_fm.xml", "High"),
    ).channels(chan_seq)

    zone_seq = Sequence()
    zones = ZoneAggregator(
        HotspotZoneGenerator(digital_channels),
        ZoneFromCallsignGenerator(digital_channels + analog_channels),
    ).zones(zone_seq)

    Codeplug(
        contact_gen,
        CountryGroupListGenerator(contact_gen.contacts(), 260),
        None,  # radio ID
        None,  # callsign
        analog_channels,
        digital_channels,
        zones,
    ).generate(open(sys.argv[1], "wt"))
