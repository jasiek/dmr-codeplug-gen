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
from datasources.przemienniki import PrzemiennikiAPI
from datasources.repeaterbook import RepeaterBookAPI
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator
from callsign_matchers import NYNJCallsignMatcher
from filters import BandFilter, sort_channels_by_distance, sort_zones_by_distance


class Recipe(BaseRecipe):
    def __init__(self, callsign, dmr_id, filename, radio_class, writer_class):
        super().__init__(callsign, dmr_id, filename, radio_class, writer_class)
        # Set location for distance sorting (New York City)
        # Latitude, Longitude for NYC area
        self.location = (40.7128, -74.0060)

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
        usa_tgs = brandmeister_contact_gen.matched_contacts("^313")
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

        # Create aggregated analog channel generator (not yet filtered)
        analog_channel_generator = ChannelAggregator(
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
        )

        # Get all analog channels
        analog_channels = analog_channel_generator.channels(chan_seq)

        # Create filtered channel lists for separate bands using BandFilter
        # 2m band (144-148 MHz)
        band_2m_filter = BandFilter(
            analog_channel_generator, frequency_ranges=[(144.0, 148.0)]
        )
        analog_2m_channels = band_2m_filter.channels(chan_seq)

        # 70cm band (420-450 MHz)
        band_70cm_filter = BandFilter(
            analog_channel_generator, frequency_ranges=[(420.0, 450.0)]
        )
        analog_70cm_channels = band_70cm_filter.channels(chan_seq)

        # Sort analog channels by distance if location is provided
        if self.location is not None:
            reference_lat, reference_lng = self.location
            analog_2m_channels = sort_channels_by_distance(
                analog_2m_channels, reference_lat, reference_lng
            )
            analog_70cm_channels = sort_channels_by_distance(
                analog_70cm_channels, reference_lat, reference_lng
            )

        self.analog_channels = analog_2m_channels + analog_70cm_channels

        # Zones
        zone_seq = Sequence()
        zones = ZoneAggregator(
            HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            AnalogZoneGenerator(analog_2m_channels, zone_name="Analog 2m"),
            AnalogZoneGenerator(analog_70cm_channels, zone_name="Analog 70cm"),
        ).zones(zone_seq)

        # Sort zones by distance if location is provided
        if self.location is not None:
            reference_lat, reference_lng = self.location
            # Collect all channels for zone sorting (digital + analog)
            all_channels = self.digital_channels + self.analog_channels
            zones = sort_zones_by_distance(
                zones, all_channels, reference_lat, reference_lng
            )

        self.zones = zones

        self.grouplists = CountryGroupListGenerator(self.contacts, 260).grouplists(
            Sequence()
        )
