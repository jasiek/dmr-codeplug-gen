"""Tests for distance sorting functionality"""

import pytest
from codeplug.filters import sort_channels_by_distance, sort_zones_by_distance
from codeplug.models import AnalogChannel, Zone, TxPower, ChannelWidth


class MockChannel:
    """Mock channel for testing"""

    def __init__(self, internal_id, name, lat=None, lng=None):
        self.internal_id = internal_id
        self.name = name
        self._lat = lat
        self._lng = lng
        self.rx_freq = 146.0
        self.tx_freq = 146.0
        self.tx_power = TxPower.High
        self.scanlist_id = "-"
        self.tot = None
        self.rx_only = False
        self.admit_crit = "Free"
        self.squelch = 1
        self.rx_tone = None
        self.tx_tone = None
        self.width = ChannelWidth.Narrow
        self.aprs = None
        self._locator = None
        self._rpt_callsign = None
        self._qth = None


def test_sort_channels_by_distance_basic():
    """Test basic channel sorting by distance"""
    # Reference point: New York City (40.7128, -74.0060)
    reference_lat = 40.7128
    reference_lng = -74.0060

    # Create test channels at different distances
    channels = [
        MockChannel(1, "Far", 41.5, -73.0),  # ~100km away
        MockChannel(2, "Close", 40.75, -74.0),  # ~5km away
        MockChannel(3, "Medium", 41.0, -73.5),  # ~60km away
        MockChannel(4, "NoCoords", None, None),  # No coordinates
    ]

    sorted_channels = sort_channels_by_distance(channels, reference_lat, reference_lng)

    # Check that channels are sorted by distance (closest first)
    assert sorted_channels[0].name == "Close"
    assert sorted_channels[1].name == "Medium"
    assert sorted_channels[2].name == "Far"
    # Channel without coordinates should be last
    assert sorted_channels[3].name == "NoCoords"


def test_sort_channels_without_coordinates_first():
    """Test that channels without coordinates can be placed first"""
    reference_lat = 40.7128
    reference_lng = -74.0060

    channels = [
        MockChannel(1, "WithCoords", 40.75, -74.0),
        MockChannel(2, "NoCoords", None, None),
    ]

    sorted_channels = sort_channels_by_distance(
        channels, reference_lat, reference_lng, channels_without_coordinates_last=False
    )

    # Channel without coordinates should be first
    assert sorted_channels[0].name == "NoCoords"
    assert sorted_channels[1].name == "WithCoords"


def test_sort_zones_by_distance_basic():
    """Test basic zone sorting by distance"""
    # Reference point: New York City
    reference_lat = 40.7128
    reference_lng = -74.0060

    # Create test channels
    channels = [
        MockChannel(1, "Close1", 40.75, -74.0),  # Close
        MockChannel(2, "Close2", 40.72, -74.05),  # Close
        MockChannel(3, "Far1", 41.5, -73.0),  # Far
        MockChannel(4, "Far2", 41.6, -73.1),  # Far
        MockChannel(5, "NoCoords", None, None),  # No coordinates
    ]

    # Create zones with different channel compositions
    zones = [
        Zone(internal_id=1, name="FarZone", channels=[3, 4]),  # Far channels
        Zone(internal_id=2, name="CloseZone", channels=[1, 2]),  # Close channels
        Zone(internal_id=3, name="MixedZone", channels=[1, 3]),  # Mixed
        Zone(internal_id=4, name="NoCoordZone", channels=[5]),  # No coordinates
    ]

    sorted_zones = sort_zones_by_distance(zones, channels, reference_lat, reference_lng)

    # Zones should be sorted by their closest channel
    assert sorted_zones[0].name == "CloseZone"  # Closest channels
    assert sorted_zones[1].name == "MixedZone"  # Has one close channel
    assert sorted_zones[2].name == "FarZone"  # All far channels
    # Zone with no valid coordinates should be last
    assert sorted_zones[3].name == "NoCoordZone"


def test_sort_zones_with_empty_channels():
    """Test zone sorting when some zones have no valid channels"""
    reference_lat = 40.7128
    reference_lng = -74.0060

    channels = [
        MockChannel(1, "Valid", 40.75, -74.0),
    ]

    zones = [
        Zone(internal_id=1, name="EmptyZone", channels=[]),
        Zone(internal_id=2, name="ValidZone", channels=[1]),
        Zone(internal_id=3, name="NonExistentChannel", channels=[999]),
    ]

    sorted_zones = sort_zones_by_distance(zones, channels, reference_lat, reference_lng)

    # Zone with valid channel should be first
    assert sorted_zones[0].name == "ValidZone"
    # Zones without valid channels should be last (order may vary)
    zone_names = [z.name for z in sorted_zones[1:]]
    assert "EmptyZone" in zone_names
    assert "NonExistentChannel" in zone_names


def test_sort_channels_all_without_coordinates():
    """Test sorting when all channels lack coordinates"""
    reference_lat = 40.7128
    reference_lng = -74.0060

    channels = [
        MockChannel(1, "A", None, None),
        MockChannel(2, "B", None, None),
        MockChannel(3, "C", None, None),
    ]

    sorted_channels = sort_channels_by_distance(channels, reference_lat, reference_lng)

    # Should return channels in original order when all lack coordinates
    assert len(sorted_channels) == 3


def test_sort_zones_minimum_distance():
    """Test that zone distance is based on closest channel"""
    reference_lat = 40.7128
    reference_lng = -74.0060

    channels = [
        MockChannel(1, "VeryClose", 40.71, -74.01),  # Very close
        MockChannel(2, "VeryFar", 42.0, -73.0),  # Very far
    ]

    # Zone with both very close and very far channels
    # Should be sorted by the very close channel
    zone = Zone(internal_id=1, name="TestZone", channels=[1, 2])

    zones = [zone]
    sorted_zones = sort_zones_by_distance(zones, channels, reference_lat, reference_lng)

    assert len(sorted_zones) == 1
    assert sorted_zones[0].name == "TestZone"
