from .usa import USABaseRecipe

from generators import Sequence
from generators.zones import (
    AnalogZoneByBandGenerator,
    ZoneFromCallsignGenerator2,
)
from generators.scanlists import StateScanListGenerator
from aggregators import ZoneAggregator
from datasources.repeaterbook import RepeaterBookAPI
from callsign_matchers import NYNJCallsignMatcher, CTCallsignMatcher, MultiMatcher

# New York City coordinates
NYC_LAT = 40.7128
NYC_LNG = -74.0060

# RepeaterBook state codes
STATE_NY = "36"  # New York
STATE_NJ = "34"  # New Jersey
STATE_CT = "09"  # Connecticut


class Recipe(USABaseRecipe):
    """NYC area codeplug recipe (100km radius covering NY/NJ/CT)."""

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

        # Set location parameters for NYC
        self.reference_lat = NYC_LAT
        self.reference_lng = NYC_LNG
        self.max_distance_km = 100.0

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister for NYC area.

        Uses callsign filtering to match NY/NJ (call district 2) and CT (call district 1)
        repeaters, then filters by distance from NYC.
        """
        usa_tgs = self.get_usa_talkgroups()

        # Create multi-matcher for NY/NJ/CT callsigns
        nyc_callsign_matcher = MultiMatcher(
            NYNJCallsignMatcher(),  # Matches call district 2 (NY/NJ)
            CTCallsignMatcher(),  # Matches call district 1 (CT)
        )

        # Generate NYC-area digital channels with callsign filtering
        nyc_digital_generator = self.create_digital_channel_generator(
            usa_tgs, callsign_matcher=nyc_callsign_matcher
        )
        self.nyc_digital_channels = nyc_digital_generator.channels(self.chan_seq)

        # Combine all digital channels
        self.digital_channels = self.nyc_digital_channels

    def generate_nyc_analog_channels(self):
        """Generate analog channels for NYC area (NY/NJ/CT)."""
        # Get repeaters from NY, NJ, and CT
        ny_repeaters = RepeaterBookAPI().get_repeaters_by_state(STATE_NY)
        nj_repeaters = RepeaterBookAPI().get_repeaters_by_state(STATE_NJ)
        ct_repeaters = RepeaterBookAPI().get_repeaters_by_state(STATE_CT)

        all_channels = []

        # Generate channels for each state
        for state_repeaters in [ny_repeaters, nj_repeaters, ct_repeaters]:
            # Generate 2m channels
            state_2m_generator = self.create_analog_channel_generator(
                state_repeaters, band_range=(144.0, 148.0)
            )
            state_2m_channels = state_2m_generator.channels(self.chan_seq)

            # Generate 70cm channels
            state_70cm_generator = self.create_analog_channel_generator(
                state_repeaters, band_range=(420.0, 450.0)
            )
            state_70cm_channels = state_70cm_generator.channels(self.chan_seq)

            all_channels.extend(state_2m_channels + state_70cm_channels)

        return all_channels

    def prepare_analog_channels(self):
        """Prepare analog channels for NYC area."""
        self.nyc_analog_channels = self.generate_nyc_analog_channels()

        self.analog_channels = (
            self.analog_aprs.channels(self.chan_seq) + self.nyc_analog_channels
        )

    def prepare_zones(self):
        """Prepare channel zones organized by callsign and band."""
        zone_seq = Sequence()
        self.zones = ZoneAggregator(
            ZoneFromCallsignGenerator2(self.digital_channels),
            AnalogZoneByBandGenerator(self.nyc_analog_channels, prefix="NYC"),
        ).zones(zone_seq)

    def prepare_scanlists(self):
        """Prepare scan lists for analog and digital channels."""
        # Create scan lists for NYC area
        nyc_scanlist_gen = StateScanListGenerator(
            "NYC", self.nyc_analog_channels, self.nyc_digital_channels
        )

        # Generate all scan lists using a single sequence to avoid ID collisions
        scanlist_seq = Sequence()
        nyc_scanlists = nyc_scanlist_gen.scanlists(scanlist_seq)

        self.scanlists = nyc_scanlists

        # Create a mapping of scanlist names to IDs for channel assignment
        scanlist_map = {}
        for scanlist in self.scanlists:
            scanlist_map[scanlist.name] = scanlist.internal_id

        # Assign scan list IDs to channels
        # NYC analog channels
        for channel in self.nyc_analog_channels:
            if "NYC Analog" in scanlist_map:
                channel.scanlist_id = scanlist_map["NYC Analog"]

        # NYC digital channels
        for channel in self.nyc_digital_channels:
            if "NYC Digital" in scanlist_map:
                channel.scanlist_id = scanlist_map["NYC Digital"]
