import sys

from generators import Sequence
from generators.aprs import AnalogAPRSGenerator
from generators.grouplists import CountryGroupListGenerator
from generators.contacts import (
    BrandmeisterTGContactGenerator,
    BrandmeisterSpecialContactGenerator,
)
from generators.analogchan import (
    AnalogPMR446ChannelGenerator,
    AnalogChannelGeneratorFromPrzemienniki,
)
from generators.digitalchan import (
    DigitalChannelGeneratorFromBrandmeister,
    HotspotDigitalChannelGenerator,
)
from generators.zones import ZoneFromCallsignGenerator2, HotspotZoneGenerator
from generators.roaming import (
    RoamingChannelGeneratorFromBrandmeister,
    RoamingZoneFromCallsignGenerator,
)
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator

from anytone import AT878UV
from writers import QDMRWriter

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("missing output file name")
        exit(1)

    contact_seq = Sequence()
    brandmeister_contact_gen = BrandmeisterTGContactGenerator()
    contacts = ContactAggregator(
        BrandmeisterSpecialContactGenerator(), brandmeister_contact_gen
    ).contacts(contact_seq)

    polish_tgs = brandmeister_contact_gen.matched_contacts("^260")
    chan_seq = Sequence()
    digital_channels = ChannelAggregator(
        HotspotDigitalChannelGenerator(polish_tgs),
        DigitalChannelGeneratorFromBrandmeister("High", polish_tgs),
    ).channels(chan_seq)

    analog_aprs = AnalogAPRSGenerator("HF2J")
    analog_channels = ChannelAggregator(
        analog_aprs,
        AnalogPMR446ChannelGenerator(),
        AnalogChannelGeneratorFromPrzemienniki("data/pl_2m_fm.xml", "High"),
        AnalogChannelGeneratorFromPrzemienniki("data/pl_70cm_fm.xml", "High"),
    ).channels(chan_seq)

    zone_seq = Sequence()
    zones = ZoneAggregator(
        HotspotZoneGenerator(digital_channels),
        ZoneFromCallsignGenerator2(digital_channels),
    ).zones(zone_seq)

    rch_seq = Sequence()
    roaming_channels = RoamingChannelGeneratorFromBrandmeister(polish_tgs).channels(
        rch_seq
    )
    roaming_zones = RoamingZoneFromCallsignGenerator(roaming_channels).zones(Sequence())

    AT878UV(
        None,
        None,
        contacts,
        CountryGroupListGenerator(contacts, 260).grouplists(Sequence()),
        analog_channels,
        digital_channels,
        zones,
        roaming_channels,
        roaming_zones,
        analog_aprs,
    ).generate(QDMRWriter(open(sys.argv[1], "wt")))
