from . import BaseRecipe

from generators import Sequence
from generators.aprs import AnalogAPRSGenerator, DigitalAPRSGenerator
from generators.grouplists import CountryGroupListGenerator
from generators.rxgrouplists import RXGroupListGenerator, HotspotRXGroupListGenerator
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
    AnalogZoneByBandGenerator,
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

# Redwood City, CA coordinates for distance filtering
REDWOOD_CITY_LAT = 37.4852
REDWOOD_CITY_LNG = -122.2364

# New York City, NY coordinates for distance filtering
NYC_LAT = 40.7128
NYC_LNG = -74.0060


class Recipe(BaseRecipe):
    def __init__(
        self, callsign, dmr_id, filename, radio_class, writer_class, timezone=None
    ):
        super().__init__(
            callsign, dmr_id, filename, radio_class, writer_class, timezone
        )

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

        self.parrot = self.bm_special_gen.parrot()

    def prepare_aprs(self):
        """Prepare APRS configurations for both digital and analog modes."""
        digital_aprs_gen = DigitalAPRSGenerator(aprs_contact=self.aprs_contact)
        self.digital_aprs_config = digital_aprs_gen.digital_aprs_config(self.aprs_seq)

        self.analog_aprs = AnalogAPRSGenerator(self.callsign)
        # Pre-generate channels to setup APRS properly
        _ = self.analog_aprs.channels(self.chan_seq)
        self.analog_aprs_config = self.analog_aprs.aprs_config_us(self.aprs_seq)

    def ca_digital_channel_generator(self, usa_tgs):
        # Create separate digital channel generators for CA and NM
        ca_digital_generator = DigitalChannelGeneratorFromBrandmeister(
            "High",
            usa_tgs,
            aprs_config=self.digital_aprs_config,
            callsign_matcher=CACallsignMatcher(),
            default_contact_id=self.bm_special_gen.parrot().internal_id,
        )

        # Apply distance filter to California digital channels (50km from Redwood City)
        ca_digital_filtered = DistanceFilter(
            ca_digital_generator,
            reference_lat=REDWOOD_CITY_LAT,
            reference_lng=REDWOOD_CITY_LNG,
            max_distance_km=50.0,
        )

        ca_digital_filtered = BandFilter(ca_digital_filtered)

        return ca_digital_filtered

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister for USA, UK, and Poland."""
        usa_tgs = self.brandmeister_contact_gen.matched_contacts("^3")
        uk_tgs = self.brandmeister_contact_gen.matched_contacts("^235")
        pl_tgs = self.brandmeister_contact_gen.matched_contacts("^260")

        # Generate hotspot channels
        # hotspot_channels = HotspotDigitalChannelGenerator(
        #    usa_tgs + uk_tgs + pl_tgs,
        #    aprs_config=self.digital_aprs_config,
        #   default_contact_id=self.bm_special_gen.parrot().internal_id,
        # ).channels(self.chan_seq)

        # Generate state-specific channels
        self.ca_digital_channels = self.ca_digital_channel_generator(usa_tgs).channels(
            self.chan_seq
        )

        # Combine all digital channels
        self.digital_channels = self.ca_digital_channels

    def generate_ca_analog_channels(self):
        # Create separate analog channel generators for CA and NM
        ca_repeaters = RepeaterBookAPI().get_repeaters_by_state("06")  # California

        ca_channel_generator_unfiltered = ChannelAggregator(
            AnalogChannelGeneratorFromRepeaterBook(
                ca_repeaters,
                "High",
                aprs=self.analog_aprs_config,
            ),
        )

        # Apply distance filter to California repeaters (50km from Redwood City)
        ca_channel_generator = DistanceFilter(
            ca_channel_generator_unfiltered,
            reference_lat=REDWOOD_CITY_LAT,
            reference_lng=REDWOOD_CITY_LNG,
            max_distance_km=50.0,
        )

        ca_2m_filter = BandFilter(
            ca_channel_generator, frequency_ranges=[(144.0, 148.0)]
        )
        ca_2m_channels = ca_2m_filter.channels(self.chan_seq)

        # CA 70cm band (420-450 MHz)
        ca_70cm_filter = BandFilter(
            ca_channel_generator, frequency_ranges=[(420.0, 450.0)]
        )
        ca_70cm_channels = ca_70cm_filter.channels(self.chan_seq)

        return ca_2m_channels + ca_70cm_channels

    def prepare_analog_channels(self):
        self.ca_analog_channels = self.generate_ca_analog_channels()

        self.analog_channels = (
            self.analog_aprs.channels(self.chan_seq) + self.ca_analog_channels
        )

    def prepare_zones(self):
        zone_seq = Sequence()
        """Prepare channel zones organized by callsign, state, band, sorted by distance."""
        self.zones = ZoneAggregator(
            ZoneFromCallsignGenerator2(self.digital_channels),
            AnalogZoneByBandGenerator(self.ca_analog_channels, prefix="CA"),
        ).zones(zone_seq)

    def prepare_scanlists(self):
        """Prepare scan lists for analog and digital channels per state."""

        # Create scan lists for CA and NM
        ca_scanlist_gen = StateScanListGenerator(
            "CA", self.ca_analog_channels, self.ca_digital_channels
        )

        # Generate all scan lists using a single sequence to avoid ID collisions
        scanlist_seq = Sequence()
        ca_scanlists = ca_scanlist_gen.scanlists(scanlist_seq)

        self.scanlists = ca_scanlists

        # Create a mapping of scanlist names to IDs for channel assignment
        scanlist_map = {}
        for scanlist in self.scanlists:
            scanlist_map[scanlist.name] = scanlist.internal_id

        # Assign scan list IDs to channels
        # CA analog channels
        for channel in self.ca_analog_channels:
            if "CA Analog" in scanlist_map:
                channel.scanlist_id = scanlist_map["CA Analog"]

        # CA digital channels
        for channel in self.ca_digital_channels:
            if "CA Digital" in scanlist_map:
                channel.scanlist_id = scanlist_map["CA Digital"]

    def prepare_grouplists(self):
        grouplist_seq = Sequence()

        # Generate RXGroupLists for repeater channels
        # This will create one group list per repeater containing all its static TGs
        self.grouplists = RXGroupListGenerator(
            self.digital_channels, self.contacts
        ).grouplists(grouplist_seq)
