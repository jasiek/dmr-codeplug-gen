from . import BaseRecipe

from generators import Sequence
from generators.grouplists import CountryGroupListGenerator
from generators.rxgrouplists import RXGroupListGenerator, HotspotRXGroupListGenerator
from generators.contacts import (
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
    FilterChain,
)

MOUNTAIN_VIEW_LAT = 37.3861
MOUNTAIN_VIEW_LNG = -122.0839

# New York City, NY coordinates for distance filtering
NYC_LAT = 40.7128
NYC_LNG = -74.0060


class Recipe(BaseRecipe):
    def __init__(
        self,
        callsign,
        dmr_id,
        filename,
        radio_class,
        writer_class,
        timezone=None,
        debug=False,
    ):
        super().__init__(
            callsign,
            dmr_id,
            filename,
            radio_class,
            writer_class,
            timezone,
            debug,
            aprs_region="US",  # USA uses US APRS frequency
        )

    def prepare_contacts(self):
        """Prepare DMR contacts including Brandmeister TGs and special contacts."""
        # Get APRS contact generator from BaseRecipe
        aprs_contact_gen = self.prepare_aprs_contacts()

        self.brandmeister_contact_gen = BrandmeisterTGContactGenerator()
        self.bm_special_gen = BrandmeisterSpecialContactGenerator()

        self.contacts = ContactAggregator(
            aprs_contact_gen,
            self.bm_special_gen,
            self.brandmeister_contact_gen,
        ).contacts(self.contact_seq)

        self.parrot = self.bm_special_gen.parrot()

    def ca_digital_channel_generator(self, usa_tgs):
        # Create filter chain for California digital channels
        ca_filter_chain = FilterChain(
            [
                DistanceFilter(
                    reference_lat=MOUNTAIN_VIEW_LAT,
                    reference_lng=MOUNTAIN_VIEW_LNG,
                    max_distance_km=50.0,
                ),
                BandFilter(),  # Default 2m and 70cm bands
            ]
        )

        # Create digital channel generator with filter chain
        ca_digital_generator = DigitalChannelGeneratorFromBrandmeister(
            "High",
            usa_tgs,
            aprs_config=self.digital_aprs_config,
            callsign_matcher=CACallsignMatcher(),
            default_contact_id=self.bm_special_gen.parrot().internal_id,
            filter_chain=ca_filter_chain,
            debug=self.debug,
        )

        return ca_digital_generator

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
        # Get California repeaters
        ca_repeaters = RepeaterBookAPI().get_repeaters_by_state("06")  # California

        # Create filter chain for CA 2m channels (distance + band)
        ca_2m_filter_chain = FilterChain(
            [
                DistanceFilter(
                    reference_lat=MOUNTAIN_VIEW_LAT,
                    reference_lng=MOUNTAIN_VIEW_LNG,
                    max_distance_km=50.0,
                ),
                BandFilter(frequency_ranges=[(144.0, 148.0)]),
            ]
        )

        # Create filter chain for CA 70cm channels (distance + band)
        ca_70cm_filter_chain = FilterChain(
            [
                DistanceFilter(
                    reference_lat=MOUNTAIN_VIEW_LAT,
                    reference_lng=MOUNTAIN_VIEW_LNG,
                    max_distance_km=50.0,
                ),
                BandFilter(frequency_ranges=[(420.0, 450.0)]),
            ]
        )

        # Generate 2m channels with filter chain
        ca_2m_generator = AnalogChannelGeneratorFromRepeaterBook(
            ca_repeaters,
            "High",
            aprs=self.analog_aprs_config,
            filter_chain=ca_2m_filter_chain,
            debug=self.debug,
        )
        ca_2m_channels = ca_2m_generator.channels(self.chan_seq)

        # Generate 70cm channels with filter chain
        ca_70cm_generator = AnalogChannelGeneratorFromRepeaterBook(
            ca_repeaters,
            "High",
            aprs=self.analog_aprs_config,
            filter_chain=ca_70cm_filter_chain,
            debug=self.debug,
        )
        ca_70cm_channels = ca_70cm_generator.channels(self.chan_seq)

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
