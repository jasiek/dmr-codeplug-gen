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
from generators.scanlists import StateScanListGenerator
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator
from datasources.przemienniki import PrzemiennikiAPI
from datasources.repeaterbook import RepeaterBookAPI
from callsign_matchers import (
    MultiMatcher,
    CACallsignMatcher,
    NMCallsignMatcher,
    NYNJCallsignMatcher,
)
from filters import (
    BandFilter,
    DistanceFilter,
    sort_channels_by_distance,
    sort_zones_by_distance,
)


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
        self.analog_aprs_config = self.analog_aprs.aprs_config_us(self.aprs_seq)

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister for USA, UK, and Poland."""
        usa_tgs = self.brandmeister_contact_gen.matched_contacts("^31")
        uk_tgs = self.brandmeister_contact_gen.matched_contacts("^235")
        pl_tgs = self.brandmeister_contact_gen.matched_contacts("^260")

        # Redwood City, CA coordinates for distance filtering
        redwood_city_lat = 37.4852
        redwood_city_lng = -122.2364

        # San Antonio, NM coordinates for distance filtering
        san_antonio_nm_lat = 33.9178
        san_antonio_nm_lng = -106.8531

        # Create separate digital channel generators for CA and NM
        ca_digital_generator = DigitalChannelGeneratorFromBrandmeister(
            "High",
            usa_tgs,
            aprs_config=self.digital_aprs_config,
            callsign_matcher=CACallsignMatcher(),
        )

        nm_digital_generator = DigitalChannelGeneratorFromBrandmeister(
            "High",
            usa_tgs,
            aprs_config=self.digital_aprs_config,
            callsign_matcher=NMCallsignMatcher(),
        )

        # Apply distance filter to California digital channels (50km from Redwood City)
        ca_digital_filtered = DistanceFilter(
            ca_digital_generator,
            reference_lat=redwood_city_lat,
            reference_lng=redwood_city_lng,
            max_distance_km=50.0,
        )

        # Apply distance filter to New Mexico digital channels (150km from San Antonio, NM)
        nm_digital_filtered = DistanceFilter(
            nm_digital_generator,
            reference_lat=san_antonio_nm_lat,
            reference_lng=san_antonio_nm_lng,
            max_distance_km=150.0,
        )

        # Generate hotspot channels
        hotspot_channels = HotspotDigitalChannelGenerator(
            usa_tgs + uk_tgs + pl_tgs,
            aprs_config=self.digital_aprs_config,
            default_contact_id=self.bm_special_gen.parrot().internal_id,
        ).channels(self.chan_seq)

        # Generate state-specific channels
        self.ca_digital_channels = ca_digital_filtered.channels(self.chan_seq)
        self.nm_digital_channels = nm_digital_filtered.channels(self.chan_seq)

        # Combine all digital channels
        self.digital_channels = (
            hotspot_channels + self.ca_digital_channels + self.nm_digital_channels
        )

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

        # Redwood City, CA coordinates for distance filtering
        redwood_city_lat = 37.4852
        redwood_city_lng = -122.2364

        # San Antonio, NM coordinates for distance filtering
        san_antonio_nm_lat = 33.9178
        san_antonio_nm_lng = -106.8531

        # Apply distance filter to California repeaters (50km from Redwood City)
        ca_channel_generator_unfiltered = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                ca_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        ca_channel_generator = DistanceFilter(
            ca_channel_generator_unfiltered,
            reference_lat=redwood_city_lat,
            reference_lng=redwood_city_lng,
            max_distance_km=50.0,
        )

        # Apply distance filter to New Mexico repeaters (150km from San Antonio, NM)
        nm_channel_generator_unfiltered = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                nm_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        nm_channel_generator = DistanceFilter(
            nm_channel_generator_unfiltered,
            reference_lat=san_antonio_nm_lat,
            reference_lng=san_antonio_nm_lng,
            max_distance_km=150.0,
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

        # Sort CA channels by distance from Redwood City (closest first)
        ca_2m_channels = sort_channels_by_distance(
            ca_2m_channels, redwood_city_lat, redwood_city_lng
        )
        ca_70cm_channels = sort_channels_by_distance(
            ca_70cm_channels, redwood_city_lat, redwood_city_lng
        )

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

        # Sort NM channels by distance from San Antonio, NM (closest first)
        nm_2m_channels = sort_channels_by_distance(
            nm_2m_channels, san_antonio_nm_lat, san_antonio_nm_lng
        )
        nm_70cm_channels = sort_channels_by_distance(
            nm_70cm_channels, san_antonio_nm_lat, san_antonio_nm_lng
        )

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
            # CA and NM channels are already sorted by their respective reference points

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
            #            + ny_2m_channels
            #            + ny_70cm_channels
            #            + nj_2m_channels
            #            + nj_70cm_channels
            + ca_2m_channels
            + ca_70cm_channels
            + nm_2m_channels
            + nm_70cm_channels
        )

    def prepare_zones(self):
        """Prepare channel zones organized by callsign, state, band, sorted by distance."""
        zones = ZoneAggregator(
            # HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            # AnalogZoneGenerator(self.ny_2m_channels, zone_name="NY 2m Analog"),
            # AnalogZoneGenerator(self.ny_70cm_channels, zone_name="NY 70cm Analog"),
            # AnalogZoneGenerator(self.nj_2m_channels, zone_name="NJ 2m Analog"),
            # AnalogZoneGenerator(self.nj_70cm_channels, zone_name="NJ 70cm Analog"),
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

    def prepare_scanlists(self):
        """Prepare scan lists for analog and digital channels per state."""
        # Combine all analog channels per state
        ca_analog_channels = self.ca_2m_channels + self.ca_70cm_channels
        nm_analog_channels = self.nm_2m_channels + self.nm_70cm_channels

        # Create scan lists for CA and NM
        ca_scanlist_gen = StateScanListGenerator(
            "CA", ca_analog_channels, self.ca_digital_channels
        )
        nm_scanlist_gen = StateScanListGenerator(
            "NM", nm_analog_channels, self.nm_digital_channels
        )

        # Generate all scan lists using a single sequence to avoid ID collisions
        scanlist_seq = Sequence()
        ca_scanlists = ca_scanlist_gen.scanlists(scanlist_seq)
        nm_scanlists = nm_scanlist_gen.scanlists(scanlist_seq)

        self.scanlists = ca_scanlists + nm_scanlists

        # Create a mapping of scanlist names to IDs for channel assignment
        scanlist_map = {}
        for scanlist in self.scanlists:
            scanlist_map[scanlist.name] = scanlist.internal_id

        # Assign scan list IDs to channels
        # CA analog channels
        for channel in ca_analog_channels:
            if "CA Analog" in scanlist_map:
                channel.scanlist_id = scanlist_map["CA Analog"]

        # CA digital channels
        for channel in self.ca_digital_channels:
            if "CA Digital" in scanlist_map:
                channel.scanlist_id = scanlist_map["CA Digital"]

        # NM analog channels
        for channel in nm_analog_channels:
            if "NM Analog" in scanlist_map:
                channel.scanlist_id = scanlist_map["NM Analog"]

        # NM digital channels
        for channel in self.nm_digital_channels:
            if "NM Digital" in scanlist_map:
                channel.scanlist_id = scanlist_map["NM Digital"]

    def prepare_grouplists(self):
        """Prepare talkgroup lists for Polish country code (260)."""
        self.grouplists = CountryGroupListGenerator(self.contacts, 260).grouplists(
            Sequence()
        )
