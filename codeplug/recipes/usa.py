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
    AnalogChannelGeneratorFromRepeaterBook,
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
from datasources.repeaterbook import RepeaterBookAPI
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator
from callsign_matchers import NYNJCallsignMatcher


class Recipe(BaseRecipe):
    def prepare(self):
        chan_seq = Sequence()

        # Contacts
        contact_seq = Sequence()
        aprs_contact_gen = APRSContactGenerator()
        aprs_contact = aprs_contact_gen.contacts(contact_seq)[0]
        brandmeister_contact_gen = BrandmeisterTGContactGenerator()

        bm_special_gen = BrandmeisterSpecialContactGenerator()
        self.contacts = ContactAggregator(
            aprs_contact_gen,
            bm_special_gen,
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
        usa_tgs = brandmeister_contact_gen.matched_contacts("^310")
        uk_tgs = brandmeister_contact_gen.matched_contacts("^235")
        self.digital_channels = ChannelAggregator(
            HotspotDigitalChannelGenerator(
                usa_tgs + uk_tgs,
                aprs_config=self.digital_aprs_config,
                default_contact_id=bm_special_gen.parrot().internal_id,
            ),
            DigitalChannelGeneratorFromBrandmeister(
                "High",
                usa_tgs,
                aprs_config=self.digital_aprs_config,
                callsign_matcher=NYNJCallsignMatcher(),
            ),
        ).channels(chan_seq)

        # Get NY and NJ analog repeaters from RepeaterBook
        repeaterbook_api = RepeaterBookAPI()
        ny_repeaters = repeaterbook_api.get_repeaters_by_state("36")  # New York
        nj_repeaters = repeaterbook_api.get_repeaters_by_state("34")  # New Jersey

        self.analog_channels = ChannelAggregator(
            analog_aprs,
            AnalogChannelGeneratorFromRepeaterBook(
                ny_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
            AnalogChannelGeneratorFromRepeaterBook(
                nj_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        ).channels(chan_seq)

        # Zones
        zone_seq = Sequence()
        self.zones = ZoneAggregator(
            HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            AnalogZoneGenerator(self.analog_channels),
        ).zones(zone_seq)

        rch_seq = Sequence()
        self.roaming_channels = RoamingChannelGeneratorFromBrandmeister(
            usa_tgs
        ).channels(rch_seq)
        self.roaming_zones = RoamingZoneFromCallsignGenerator(
            self.roaming_channels
        ).zones(Sequence())
        self.grouplists = CountryGroupListGenerator(self.contacts, 260).grouplists(
            Sequence()
        )
