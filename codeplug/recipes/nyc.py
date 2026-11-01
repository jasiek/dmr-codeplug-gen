from .usa import USABaseRecipe

from generators import Sequence
from generators.zones import (
    AnalogZoneByBandGenerator,
    ZoneFromCallsignGenerator2,
)
from generators.scanlists import StateScanListGenerator
from aggregators import ZoneAggregator
from lxml import etree

from datasources.repeaterbook import RepeaterBookAPI, qth_state_county, split_rxf
from callsign_matchers import NYNJCallsignMatcher, CTCallsignMatcher, MultiMatcher
from filters import AnyFilter, RegionFilter

# New York City coordinates
NYC_LAT = 40.7128
NYC_LNG = -74.0060

# Eastern Long Island (Suffolk east of ~Riverhead out to Montauk/Orient Point)
# lies beyond the NYC radius. The box starts west of where the NYC circle
# stops covering the island, so there is no gap. Its north edge sits in
# Long Island Sound: Orient Point is 41.16N, while the CT shore opposite
# (Milford through New London) is 41.22N and up.
LONG_ISLAND_BOUNDS = dict(min_lat=40.55, max_lat=41.2, min_lng=-73.2, max_lng=-71.8)

# RepeaterBook search circle covering the box above
LONG_ISLAND_SEARCH = (40.95, -72.45, 70.0)

LONG_ISLAND_COUNTIES = {"Nassau", "Suffolk"}

# Analog zones and scan lists are built per region, in this order
ANALOG_REGIONS = ("NYC", "NJ", "LI")


class Recipe(USABaseRecipe):
    """NYC area codeplug recipe (100km radius covering NY/NJ/CT, plus all of Long Island)."""

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

    def location_filter(self):
        """NYC radius plus the rest of Long Island."""
        return AnyFilter(
            [super().location_filter(), RegionFilter(**LONG_ISLAND_BOUNDS)]
        )

    def repeaters(self, modes=("fm",)):
        """RepeaterBook listings for the NYC radius and eastern Long Island."""
        return RepeaterBookAPI().repeaters_near_any(
            [
                (self.reference_lat, self.reference_lng, self.max_distance_km),
                LONG_ISLAND_SEARCH,
            ],
            modes=modes,
        )

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister for NYC area.

        Uses callsign filtering to match NY/NJ (call district 2) and CT (call district 1)
        repeaters, then filters to the NYC radius plus Long Island. RepeaterBook DMR
        listings in that area are cross-checked against BM to pick up repeaters that BM
        lists as hotspots or with bad coordinates.
        """
        usa_tgs = self.get_usa_talkgroups()

        # Create multi-matcher for NY/NJ/CT callsigns
        nyc_callsign_matcher = MultiMatcher(
            NYNJCallsignMatcher(),  # Matches call district 2 (NY/NJ)
            CTCallsignMatcher(),  # Matches call district 1 (CT)
        )

        # Generate NYC-area digital channels with callsign filtering
        dmr_repeaters = self.repeaters(modes=("dmr",))
        nyc_digital_generator = self.create_digital_channel_generator(
            usa_tgs, callsign_matcher=nyc_callsign_matcher, repeaterbook=dmr_repeaters
        )
        self.nyc_digital_channels = nyc_digital_generator.channels(self.chan_seq)

        # Combine all digital channels
        self.digital_channels = self.nyc_digital_channels

    def analog_repeaters_by_region(self):
        """RepeaterBook FM listings split into ANALOG_REGIONS."""
        parts = split_rxf(self.repeaters(), analog_region)
        empty = etree.fromstring("<rxf><repeaters/></rxf>")
        return {region: parts.get(region, empty) for region in ANALOG_REGIONS}

    def generate_analog_channels(self, repeaters):
        """2m and 70cm channels for one region's repeaters."""
        return self.create_analog_channel_generator(repeaters).channels(self.chan_seq)

    def prepare_analog_channels(self):
        """Prepare analog channels for NYC, NJ and Long Island."""
        self.regional_analog_channels = {
            region: self.generate_analog_channels(repeaters)
            for region, repeaters in self.analog_repeaters_by_region().items()
        }
        self.nyc_analog_channels = [
            chan for chans in self.regional_analog_channels.values() for chan in chans
        ]

        self.analog_channels = (
            self.analog_aprs.channels(self.chan_seq) + self.nyc_analog_channels
        )

    def prepare_zones(self):
        """Per-repeater digital zones, plus per-band analog zones for each region."""
        zone_seq = Sequence()
        self.zones = ZoneAggregator(
            ZoneFromCallsignGenerator2(self.digital_channels),
            *(
                AnalogZoneByBandGenerator(channels, prefix=region)
                for region, channels in self.regional_analog_channels.items()
            ),
        ).zones(zone_seq)

    def prepare_scanlists(self):
        """One analog scan list per region, plus one for all digital channels."""
        scanlist_seq = Sequence()
        self.scanlists = []
        for region, channels in self.regional_analog_channels.items():
            digital = self.nyc_digital_channels if region == "NYC" else []
            self.scanlists += StateScanListGenerator(
                region, channels, digital
            ).scanlists(scanlist_seq)

        scanlist_map = {
            scanlist.name: scanlist.internal_id for scanlist in self.scanlists
        }

        for region, channels in self.regional_analog_channels.items():
            for channel in channels:
                if f"{region} Analog" in scanlist_map:
                    channel.scanlist_id = scanlist_map[f"{region} Analog"]

        for channel in self.nyc_digital_channels:
            if "NYC Digital" in scanlist_map:
                channel.scanlist_id = scanlist_map["NYC Digital"]


def analog_region(node):
    """
    Zone region for a RepeaterBook listing: "NJ" for New Jersey, "LI" for
    Nassau/Suffolk, and "NYC" for everything else (the five boroughs,
    Westchester and the Hudson Valley, and nearby CT/PA).
    """
    state, county = qth_state_county(node)
    if state == "New Jersey":
        return "NJ"
    if state == "New York" and county in LONG_ISLAND_COUNTIES:
        return "LI"
    return "NYC"
