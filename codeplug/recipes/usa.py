from . import BaseRecipe

from generators import Sequence
from generators.rxgrouplists import RXGroupListGenerator
from generators.contacts import (
    BrandmeisterTGContactGenerator,
    BrandmeisterSpecialContactGenerator,
)
from generators.analogchan import (
    AnalogChannelGeneratorFromRepeaterBook,
)
from generators.digitalchan import (
    DigitalChannelGeneratorFromBrandmeister,
)
from generators.zones import (
    AnalogZoneByBandGenerator,
    ZoneFromCallsignGenerator2,
)
from generators.scanlists import StateScanListGenerator
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator
from datasources.przemienniki import PrzemiennikiAPI
from datasources.repeaterbook import RepeaterBookAPI
from callsign_matchers import (
    CACallsignMatcher,
)
from filters import (
    BandFilter,
    DistanceFilter,
    FilterChain,
)

MOUNTAIN_VIEW_LAT = 37.3861
MOUNTAIN_VIEW_LNG = -122.0839


class USABaseRecipe(BaseRecipe):
    """Base class for all USA codeplug recipes."""

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

        # Subclasses should set these
        self.reference_lat = None
        self.reference_lng = None
        self.max_distance_km = None

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

    def get_usa_talkgroups(self):
        """Get USA Brandmeister talkgroups (3xxx)."""
        return self.brandmeister_contact_gen.matched_contacts("^3")

    def get_uk_talkgroups(self):
        """Get UK Brandmeister talkgroups (235xxx)."""
        return self.brandmeister_contact_gen.matched_contacts("^235")

    def get_poland_talkgroups(self):
        """Get Poland Brandmeister talkgroups (260xxx)."""
        return self.brandmeister_contact_gen.matched_contacts("^260")

    def create_digital_channel_generator(
        self, talkgroups, callsign_matcher=None, bands=None
    ):
        """
        Create a digital channel generator with location-based filtering.

        Args:
            talkgroups: List of talkgroup contacts
            callsign_matcher: Optional callsign matcher for filtering
            bands: Optional band filter ranges, defaults to 2m and 70cm
        """
        if self.reference_lat is None or self.reference_lng is None:
            raise ValueError("reference_lat and reference_lng must be set in subclass")

        if self.max_distance_km is None:
            raise ValueError("max_distance_km must be set in subclass")

        # Create filter chain
        filters = [
            DistanceFilter(
                reference_lat=self.reference_lat,
                reference_lng=self.reference_lng,
                max_distance_km=self.max_distance_km,
            ),
            BandFilter(frequency_ranges=bands) if bands else BandFilter(),
        ]

        filter_chain = FilterChain(filters)

        # Create digital channel generator with filter chain
        return DigitalChannelGeneratorFromBrandmeister(
            "High",
            talkgroups=talkgroups,
            aprs_config=self.digital_aprs_config,
            callsign_matcher=callsign_matcher,
            default_contact_id=self.bm_special_gen.parrot().internal_id,
            filter_chain=filter_chain,
            debug=self.debug,
        )

    def create_analog_channel_generator(self, repeaters, band_range):
        """
        Create an analog channel generator with location and band filtering.

        Args:
            repeaters: List of repeater data from RepeaterBook
            band_range: Tuple of (min_freq, max_freq) in MHz
        """
        if self.reference_lat is None or self.reference_lng is None:
            raise ValueError("reference_lat and reference_lng must be set in subclass")

        if self.max_distance_km is None:
            raise ValueError("max_distance_km must be set in subclass")

        # Create filter chain
        filter_chain = FilterChain(
            [
                DistanceFilter(
                    reference_lat=self.reference_lat,
                    reference_lng=self.reference_lng,
                    max_distance_km=self.max_distance_km,
                ),
                BandFilter(frequency_ranges=[band_range]),
            ]
        )

        # Generate channels with filter chain
        return AnalogChannelGeneratorFromRepeaterBook(
            repeaters,
            "High",
            aprs=self.analog_aprs_config,
            filter_chain=filter_chain,
            debug=self.debug,
        )

    def prepare_grouplists(self):
        """Prepare RXGroupLists for repeater channels."""
        grouplist_seq = Sequence()

        # Generate RXGroupLists for repeater channels
        # This will create one group list per repeater containing all its static TGs
        self.grouplists = RXGroupListGenerator(
            self.digital_channels, self.contacts
        ).grouplists(grouplist_seq)


class Recipe(USABaseRecipe):
    """California/Mountain View codeplug recipe (50km radius)."""

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
        )

        # Set location parameters for Mountain View, CA
        self.reference_lat = MOUNTAIN_VIEW_LAT
        self.reference_lng = MOUNTAIN_VIEW_LNG
        self.max_distance_km = 50.0

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister for USA."""
        usa_tgs = self.get_usa_talkgroups()

        # Generate California-specific channels
        ca_digital_generator = self.create_digital_channel_generator(
            usa_tgs, callsign_matcher=CACallsignMatcher()
        )
        self.ca_digital_channels = ca_digital_generator.channels(self.chan_seq)

        # Combine all digital channels
        self.digital_channels = self.ca_digital_channels

    def generate_ca_analog_channels(self):
        """Generate analog channels for California."""
        # Get California repeaters
        ca_repeaters = RepeaterBookAPI().get_repeaters_by_state("06")  # California

        # Generate 2m channels
        ca_2m_generator = self.create_analog_channel_generator(
            ca_repeaters, band_range=(144.0, 148.0)
        )
        ca_2m_channels = ca_2m_generator.channels(self.chan_seq)

        # Generate 70cm channels
        ca_70cm_generator = self.create_analog_channel_generator(
            ca_repeaters, band_range=(420.0, 450.0)
        )
        ca_70cm_channels = ca_70cm_generator.channels(self.chan_seq)

        return ca_2m_channels + ca_70cm_channels

    def prepare_analog_channels(self):
        """Prepare analog channels for California."""
        self.ca_analog_channels = self.generate_ca_analog_channels()

        self.analog_channels = (
            self.analog_aprs.channels(self.chan_seq) + self.ca_analog_channels
        )

    def prepare_zones(self):
        """Prepare channel zones organized by callsign, state, band, sorted by distance."""
        zone_seq = Sequence()
        self.zones = ZoneAggregator(
            ZoneFromCallsignGenerator2(self.digital_channels),
            AnalogZoneByBandGenerator(self.ca_analog_channels, prefix="CA"),
        ).zones(zone_seq)

    def prepare_scanlists(self):
        """Prepare scan lists for analog and digital channels per state."""
        # Create scan lists for CA
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
