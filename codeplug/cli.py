import sys

from codeplug import Codeplug
from generators import (
    BrandmeisterTGContactGenerator,
    CountryGroupListGenerator,
    ChannelCombinator,
    AnalogChannelGeneratorFromPrzemienniki,
    DigitalChannelGeneratorFromBrandmeister,
)

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
        ChannelCombinator(
            AnalogChannelGeneratorFromPrzemienniki("data/pl_2m_fm.xml", "High"),
            AnalogChannelGeneratorFromPrzemienniki("data/pl_70cm_fm.xml", "High"),
        ),
        DigitalChannelGeneratorFromBrandmeister("data/bm_2602.json", "High"),
    ).generate(open(sys.argv[1], "wt"))
