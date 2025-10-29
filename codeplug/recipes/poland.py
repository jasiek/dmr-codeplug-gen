from . import BaseRecipe

from generators import Sequence
from generators.aprs import AnalogAPRSGenerator, DigitalAPRSGenerator
from generators.grouplists import CountryGroupListGenerator
from generators.contacts import (
    APRSDigitalContactGenerator,
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
from datasources.przemienniki import PrzemiennikiAPI
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator
from callsign_matchers import RegexMatcher


class Recipe(BaseRecipe):
    def prepare_contacts(self):
        """Prepare DMR contacts including APRS, Brandmeister TGs, and special contacts."""
        aprs_contact_gen = APRSDigitalContactGenerator()
        self.aprs_contact = aprs_contact_gen.contacts(self.contact_seq)[0]
        self.brandmeister_contact_gen = BrandmeisterTGContactGenerator()
        self.bm_special_gen = BrandmeisterSpecialContactGenerator()

        self.contacts = ContactAggregator(
            aprs_contact_gen,
            self.bm_special_gen,
            self.brandmeister_contact_gen,
        ).contacts(self.contact_seq)

    def prepare_aprs(self):
        """Prepare APRS configurations for both digital and analog modes."""
        digital_aprs_gen = DigitalAPRSGenerator(aprs_contact=self.aprs_contact)
        self.digital_aprs_config = digital_aprs_gen.digital_aprs_config(self.aprs_seq)

        self.analog_aprs = AnalogAPRSGenerator(self.callsign)
        # Pre-generate channels to setup APRS properly
        _ = self.analog_aprs.channels(self.chan_seq)
        self.analog_aprs_config = self.analog_aprs.aprs_config_eu(self.aprs_seq)

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister and hotspot."""
        polish_tgs = self.brandmeister_contact_gen.matched_contacts("^260")
        uk_tgs = self.brandmeister_contact_gen.matched_contacts("^235")

        self.digital_channels = ChannelAggregator(
            HotspotDigitalChannelGenerator(
                polish_tgs + uk_tgs,
                aprs_config=self.digital_aprs_config,
                default_contact_id=self.bm_special_gen.parrot().internal_id,
            ),
            DigitalChannelGeneratorFromBrandmeister(
                "High",
                polish_tgs,
                aprs_config=self.digital_aprs_config,
                callsign_matcher=RegexMatcher(r"^S[P0-9]"),
            ),
        ).channels(self.chan_seq)

    def prepare_analog_channels(self):
        """Prepare analog (FM) channels from Przemienniki and PMR446."""
        self.analog_pmr_chan_gen = AnalogPMR446ChannelGenerator(
            aprs=self.analog_aprs_config
        )

        self.analog_channels = ChannelAggregator(
            self.analog_aprs,
            self.analog_pmr_chan_gen,
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
        ).channels(self.chan_seq)

    def prepare_zones(self):
        """Prepare channel zones organized by callsign and type."""
        self.zones = ZoneAggregator(
            HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            PMRZoneGenerator(self.analog_pmr_chan_gen.channels(None)),
            AnalogZoneGenerator(self.analog_channels),
        ).zones(self.zone_seq)

    def prepare_roaming(self):
        """Prepare roaming channels and zones for Polish repeaters."""
        polish_tgs = self.brandmeister_contact_gen.matched_contacts("^260")
        self.roaming_channels = RoamingChannelGeneratorFromBrandmeister(
            polish_tgs
        ).channels(self.rch_seq)
        self.roaming_zones = RoamingZoneFromCallsignGenerator(
            self.roaming_channels
        ).zones(Sequence())

    def prepare_grouplists(self):
        """Prepare talkgroup lists for Polish country code (260)."""
        self.grouplists = CountryGroupListGenerator(self.contacts, 260).grouplists(
            Sequence()
        )
