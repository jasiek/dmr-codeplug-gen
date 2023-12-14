import sys

from codeplug import Codeplug
from generators import (
    BrandmeisterTGContactGenerator,
    CountryGroupListGenerator,
    ChannelCombinator,
    AnalogChannelGeneratorFromPrzemienniki,
)

if __name__ == "__main__":
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
    ).generate(sys.stdout)
