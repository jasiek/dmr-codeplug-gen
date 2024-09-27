from . import BaseRecipe

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
from datasources.przemienniki import PrzemiennikiAPI


class Recipe(BaseRecipe):
    def prepare(self):
        chan_seq = Sequence()

        # Contacts
        contact_seq = Sequence()
        aprs_contact_gen = APRSContactGenerator()
        aprs_contact = aprs_contact_gen.contacts(contact_seq)[0]
        brandmeister_contact_gen = BrandmeisterTGContactGenerator()

        self.contacts = ContactAggregator(
            aprs_contact_gen,
            BrandmeisterSpecialContactGenerator(),
            brandmeister_contact_gen,
        ).contacts(contact_seq)

        # APRS
        aprs_seq = Sequence()
        digital_aprs_gen = DigitalAPRSGenerator(aprs_contact=aprs_contact)
        self.digital_aprs_config = digital_aprs_gen.aprs(aprs_seq)
        analog_aprs = AnalogAPRSGenerator(self.callsign)
        _ = analog_aprs.channels(
            chan_seq
        )  # This is a bit of a hack, it will pre-generate channels
        self.analog_aprs_config = analog_aprs.aprs(aprs_seq)

        # Channels
        polish_tgs = brandmeister_contact_gen.matched_contacts("^260")
        self.digital_channels = ChannelAggregator(
            HotspotDigitalChannelGenerator(
                polish_tgs, aprs_config=self.digital_aprs_config
            ),
            DigitalChannelGeneratorFromBrandmeister(
                "High", polish_tgs, aprs_config=self.digital_aprs_config
            ),
        ).channels(chan_seq)
        analog_pmr_chan_gen = AnalogPMR446ChannelGenerator(aprs=self.analog_aprs_config)
        self.analog_channels = ChannelAggregator(
            analog_aprs,
            analog_pmr_chan_gen,
            AnalogChannelGeneratorFromPrzemienniki(
                PrzemiennikiAPI().repeaters_2m(),
                "High",
                aprs=self.analog_aprs_config,
            ),
            AnalogChannelGeneratorFromPrzemienniki(
                PrzemiennikiAPI().repeaters_70cm(),
                "High",
                aprs=self.analog_aprs_config,
            ),
        ).channels(chan_seq)

        # Zones
        zone_seq = Sequence()
        self.zones = ZoneAggregator(
            HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            PMRZoneGenerator(analog_pmr_chan_gen.channels(None)),
            AnalogZoneGenerator(self.analog_channels),
        ).zones(zone_seq)

        rch_seq = Sequence()
        self.roaming_channels = RoamingChannelGeneratorFromBrandmeister(
            polish_tgs
        ).channels(rch_seq)
        self.roaming_zones = RoamingZoneFromCallsignGenerator(
            self.roaming_channels
        ).zones(Sequence())
        self.grouplists = CountryGroupListGenerator(self.contacts, 260).grouplists(
            Sequence()
        )
