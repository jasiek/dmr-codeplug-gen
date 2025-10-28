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
    def __init__(
        self, callsign, dmr_id, filename, radio_class, writer_class, timezone=None
    ):
        super().__init__(
            callsign, dmr_id, filename, radio_class, writer_class, timezone
        )
        # Set location for distance sorting (New York City)
        # Latitude, Longitude for NYC area
        self.location = (40.7128, -74.0060)

    def prepare_contacts(self):
        """Prepare DMR contacts including APRS, Brandmeister TGs, and special contacts."""
        aprs_contact_gen = APRSContactGenerator()
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
        self.digital_aprs_config = digital_aprs_gen.aprs(self.aprs_seq)

        self.analog_aprs = AnalogAPRSGenerator(self.callsign)
        # Pre-generate channels to setup APRS properly
        _ = self.analog_aprs.channels(self.chan_seq)
        self.analog_aprs_config = self.analog_aprs.aprs(self.aprs_seq)

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister for USA, UK, and Poland."""
        usa_tgs = self.brandmeister_contact_gen.matched_contacts("^31")
        uk_tgs = self.brandmeister_contact_gen.matched_contacts("^235")
        pl_tgs = self.brandmeister_contact_gen.matched_contacts("^260")

        self.digital_channels = ChannelAggregator(
            HotspotDigitalChannelGenerator(
                usa_tgs + uk_tgs + pl_tgs,
                aprs_config=self.digital_aprs_config,
                default_contact_id=self.bm_special_gen.parrot().internal_id,
            ),
            DigitalChannelGeneratorFromBrandmeister(
                "High",
                usa_tgs,
                aprs_config=self.digital_aprs_config,
                callsign_matcher=NYNJCallsignMatcher(),
            ),
        ).channels(self.chan_seq)

    def prepare_analog_channels(self):
        """Prepare analog (FM) channels from RepeaterBook for NY/NJ/CA/NM, filtered and sorted by distance."""
        # Get analog repeaters from RepeaterBook for each state
        repeaterbook_api = RepeaterBookAPI()
        ny_repeaters = repeaterbook_api.get_repeaters_by_state("36")  # New York
        nj_repeaters = repeaterbook_api.get_repeaters_by_state("34")  # New Jersey
        ca_repeaters = repeaterbook_api.get_repeaters_by_state("06")  # California
        nm_repeaters = repeaterbook_api.get_repeaters_by_state("35")  # New Mexico

        # Create separate channel generators for each state
        ny_channel_generator = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                ny_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        nj_channel_generator = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                nj_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        ca_channel_generator = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                ca_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        nm_channel_generator = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                nm_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        # Create filtered channel lists for NY by band
        # NY 2m band (144-148 MHz)
        ny_2m_filter = BandFilter(
            ny_channel_generator, frequency_ranges=[(144.0, 148.0)]
        )
        ny_2m_channels = ny_2m_filter.channels(self.chan_seq)

        # NY 70cm band (420-450 MHz)
        ny_70cm_filter = BandFilter(
            ny_channel_generator, frequency_ranges=[(420.0, 450.0)]
        )
        ny_70cm_channels = ny_70cm_filter.channels(self.chan_seq)

        # Create filtered channel lists for NJ by band
        # NJ 2m band (144-148 MHz)
        nj_2m_filter = BandFilter(
            nj_channel_generator, frequency_ranges=[(144.0, 148.0)]
        )
        nj_2m_channels = nj_2m_filter.channels(self.chan_seq)

        # NJ 70cm band (420-450 MHz)
        nj_70cm_filter = BandFilter(
            nj_channel_generator, frequency_ranges=[(420.0, 450.0)]
        )
        nj_70cm_channels = nj_70cm_filter.channels(self.chan_seq)

        # Create filtered channel lists for CA by band
        # CA 2m band (144-148 MHz)
        ca_2m_filter = BandFilter(
            ca_channel_generator, frequency_ranges=[(144.0, 148.0)]
        )
        ca_2m_channels = ca_2m_filter.channels(self.chan_seq)

        # CA 70cm band (420-450 MHz)
        ca_70cm_filter = BandFilter(
            ca_channel_generator, frequency_ranges=[(420.0, 450.0)]
        )
        ca_70cm_channels = ca_70cm_filter.channels(self.chan_seq)

        # Create filtered channel lists for NM by band
        # NM 2m band (144-148 MHz)
        nm_2m_filter = BandFilter(
            nm_channel_generator, frequency_ranges=[(144.0, 148.0)]
        )
        nm_2m_channels = nm_2m_filter.channels(self.chan_seq)

        # NM 70cm band (420-450 MHz)
        nm_70cm_filter = BandFilter(
            nm_channel_generator, frequency_ranges=[(420.0, 450.0)]
        )
        nm_70cm_channels = nm_70cm_filter.channels(self.chan_seq)

        # Sort analog channels by distance if location is provided
        if self.location is not None:
            reference_lat, reference_lng = self.location
            ny_2m_channels = sort_channels_by_distance(
                ny_2m_channels, reference_lat, reference_lng
            )
            ny_70cm_channels = sort_channels_by_distance(
                ny_70cm_channels, reference_lat, reference_lng
            )
            nj_2m_channels = sort_channels_by_distance(
                nj_2m_channels, reference_lat, reference_lng
            )
            nj_70cm_channels = sort_channels_by_distance(
                nj_70cm_channels, reference_lat, reference_lng
            )
            ca_2m_channels = sort_channels_by_distance(
                ca_2m_channels, reference_lat, reference_lng
            )
            ca_70cm_channels = sort_channels_by_distance(
                ca_70cm_channels, reference_lat, reference_lng
            )
            nm_2m_channels = sort_channels_by_distance(
                nm_2m_channels, reference_lat, reference_lng
            )
            nm_70cm_channels = sort_channels_by_distance(
                nm_70cm_channels, reference_lat, reference_lng
            )

        # Store separated channels for zone generation
        self.ny_2m_channels = ny_2m_channels
        self.ny_70cm_channels = ny_70cm_channels
        self.nj_2m_channels = nj_2m_channels
        self.nj_70cm_channels = nj_70cm_channels
        self.ca_2m_channels = ca_2m_channels
        self.ca_70cm_channels = ca_70cm_channels
        self.nm_2m_channels = nm_2m_channels
        self.nm_70cm_channels = nm_70cm_channels

        # Combine all analog channels
        self.analog_channels = (
            self.analog_aprs.channels(self.chan_seq)
            + ny_2m_channels
            + ny_70cm_channels
            + nj_2m_channels
            + nj_70cm_channels
            + ca_2m_channels
            + ca_70cm_channels
            + nm_2m_channels
            + nm_70cm_channels
        )

    def prepare_zones(self):
        """Prepare channel zones organized by callsign, state, band, sorted by distance."""
        zones = ZoneAggregator(
            HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            AnalogZoneGenerator(self.ny_2m_channels, zone_name="NY 2m Analog"),
            AnalogZoneGenerator(self.ny_70cm_channels, zone_name="NY 70cm Analog"),
            AnalogZoneGenerator(self.nj_2m_channels, zone_name="NJ 2m Analog"),
            AnalogZoneGenerator(self.nj_70cm_channels, zone_name="NJ 70cm Analog"),
            AnalogZoneGenerator(self.ca_2m_channels, zone_name="CA 2m Analog"),
            AnalogZoneGenerator(self.ca_70cm_channels, zone_name="CA 70cm Analog"),
            AnalogZoneGenerator(self.nm_2m_channels, zone_name="NM 2m Analog"),
            AnalogZoneGenerator(self.nm_70cm_channels, zone_name="NM 70cm Analog"),
        ).zones(self.zone_seq)

        # Sort zones by distance if location is provided
        if self.location is not None:
            reference_lat, reference_lng = self.location
            # Collect all channels for zone sorting (digital + analog)
            all_channels = self.digital_channels + self.analog_channels
            zones = sort_zones_by_distance(
                zones, all_channels, reference_lat, reference_lng
            )

        self.zones = zones

    def prepare_grouplists(self):
        """Prepare talkgroup lists for Polish country code (260)."""
        self.grouplists = CountryGroupListGenerator(self.contacts, 260).grouplists(
            Sequence()
        )
