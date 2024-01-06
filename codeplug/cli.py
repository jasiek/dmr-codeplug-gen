import sys

from generators import Sequence
from generators.aprs import AnalogAPRSGenerator, DigitalAPRSGenerator
from generators.grouplists import CountryGroupListGenerator
from generators.contacts import (
    APRSContactGenerator,
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
from generators.zones import (
    ZoneFromCallsignGenerator2,
    HotspotZoneGenerator,
    PMRZoneGenerator,
    AnalogZoneGenerator,
)
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
    aprs_contact_gen = APRSContactGenerator()
    aprs_contact = aprs_contact_gen.contacts(contact_seq)[0]

    contacts = ContactAggregator(
        aprs_contact_gen,
        BrandmeisterSpecialContactGenerator(),
        brandmeister_contact_gen,
    ).contacts(contact_seq)

    polish_tgs = brandmeister_contact_gen.matched_contacts("^260")
    chan_seq = Sequence()

    # APRS
    aprs_seq = Sequence()
    digital_aprs_gen = DigitalAPRSGenerator(aprs_contact=aprs_contact)
    digital_aprs_config = digital_aprs_gen.aprs(aprs_seq)
    analog_aprs = AnalogAPRSGenerator("HF2J")
    _ = analog_aprs.channels(
        chan_seq
    )  # This is a bit of a hack, it will pre-generate channels
    analog_aprs_config = analog_aprs.aprs(aprs_seq)

    # Channels
    digital_channels = ChannelAggregator(
        HotspotDigitalChannelGenerator(polish_tgs, aprs_config=digital_aprs_config),
        DigitalChannelGeneratorFromBrandmeister(
            "High", polish_tgs, aprs_config=digital_aprs_config
        ),
    ).channels(chan_seq)

    analog_pmr_chan_gen = AnalogPMR446ChannelGenerator(aprs=analog_aprs_config)
    analog_channels = ChannelAggregator(
        analog_aprs,
        analog_pmr_chan_gen,
        AnalogChannelGeneratorFromPrzemienniki(
            "data/pl_2m_fm.xml",
            "High",
            aprs=analog_aprs_config,
        ),
        AnalogChannelGeneratorFromPrzemienniki(
            "data/pl_70cm_fm.xml",
            "High",
            aprs=analog_aprs_config,
        ),
    ).channels(chan_seq)

    zone_seq = Sequence()
    zones = ZoneAggregator(
        HotspotZoneGenerator(digital_channels),
        ZoneFromCallsignGenerator2(digital_channels),
        PMRZoneGenerator(analog_pmr_chan_gen.channels(None)),
        AnalogZoneGenerator(analog_channels),
    ).zones(zone_seq)

    rch_seq = Sequence()
    roaming_channels = RoamingChannelGeneratorFromBrandmeister(polish_tgs).channels(
        rch_seq
    )
    roaming_zones = RoamingZoneFromCallsignGenerator(roaming_channels).zones(Sequence())

    AT878UV(
        dmr_id=2601823,
        callsign="HF2J",
        contacts=contacts,
        grouplists=CountryGroupListGenerator(contacts, 260).grouplists(Sequence()),
        analog_channels=analog_channels,
        digital_channels=digital_channels,
        zones=zones,
        roaming_channels=roaming_channels,
        roaming_zones=roaming_zones,
        analog_aprs_config=analog_aprs_config,
        digital_aprs_config=digital_aprs_config,
    ).generate(QDMRWriter(open(sys.argv[1], "wt")))
