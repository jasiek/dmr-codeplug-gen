import sys

from codeplug import Codeplug

from generators.grouplists import CountryGroupListGenerator
from generators.contacts import BrandmeisterTGContactGenerator
from generators.channels import (
    AnalogChannelGeneratorFromPrzemienniki,
    DigitalChannelGeneratorFromBrandmeister,
    HotspotDigitalChannelGenerator,
)
from aggregators import ChannelAggregator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("missing output file name")
        exit(1)

    contact_gen = BrandmeisterTGContactGenerator()
    Codeplug(
        contact_gen,
        CountryGroupListGenerator(contact_gen.contacts(), 260),
        31337,
        "LOLCALL",
        ChannelAggregator(
            AnalogChannelGeneratorFromPrzemienniki("data/pl_2m_fm.xml", "High"),
            AnalogChannelGeneratorFromPrzemienniki("data/pl_70cm_fm.xml", "High"),
        ),
        ChannelAggregator(
            HotspotDigitalChannelGenerator(contact_gen.prefixed_contacts("260")),
            DigitalChannelGeneratorFromBrandmeister("data/bm_2602.json", "High"),
        ),
    ).generate(open(sys.argv[1], "wt"))
