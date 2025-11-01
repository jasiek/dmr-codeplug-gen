#!/usr/bin/env python3
"""
Test script for the new location-based zone generators.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "codeplug"))

from generators import Sequence
from generators.location_zones import (
    LocationClusterZoneGenerator,
    DistanceBandedZoneGenerator,
)
from models import DigitalChannel, AnalogChannel


def create_test_channel(name, lat, lng, rpt_callsign=None, qth=None, channel_id=1):
    """Create a test channel with location data."""
    # Create a basic digital channel for testing
    channel = DigitalChannel(
        internal_id=channel_id,
        name=name,
        rx_freq=439.0,  # 70cm frequency
        tx_freq=439.0,
        tx_power="High",
        scanlist_id=None,
        tot=180,
        rx_only=False,
        admit_crit="Always",
        color=1,
        slot=1,
        rx_grouplist_id=None,
        tx_contact_id=None,
        aprs=None,
        anytone=None,
        _lat=lat,
        _lng=lng,
        _locator=None,
        _rpt_callsign=rpt_callsign,
        _qth=qth,
    )
    return channel


def test_location_clustering():
    """Test the LocationClusterZoneGenerator."""
    print("Testing LocationClusterZoneGenerator...")

    # Create test channels in a cluster (within 25km of each other)
    nyc_area_channels = [
        create_test_channel("W2ABC NYC", 40.7128, -74.0060, "W2ABC", "New York", 1),
        create_test_channel(
            "W2DEF Manhattan", 40.7505, -73.9934, "W2DEF", "Manhattan", 2
        ),
        create_test_channel(
            "W2GHI Brooklyn", 40.6782, -73.9442, "W2GHI", "Brooklyn", 3
        ),
    ]

    # Create a distant channel
    sf_channel = [
        create_test_channel("W6XYZ SF", 37.7749, -122.4194, "W6XYZ", "San Francisco", 4)
    ]

    all_channels = nyc_area_channels + sf_channel

    # Test with default settings (25km max distance)
    generator = LocationClusterZoneGenerator(
        channels=all_channels,
        max_distance_km=25.0,
        min_repeaters_per_zone=2,
        zone_naming="representative",
    )

    seq = Sequence()
    zones = generator.zones(seq)

    print(f"Generated {len(zones)} zones:")
    for zone in zones:
        print(f"  - {zone.name}: {len(zone.channels)} channels")
        for channel_id in zone.channels:
            channel = next(c for c in all_channels if c.internal_id == channel_id)
            print(f"    • {channel.name} ({channel._lat:.3f}, {channel._lng:.3f})")

    # Should create 2 zones: NYC cluster (3 channels) and SF alone (excluded due to min_repeaters=2)
    assert len(zones) == 1, f"Expected 1 zone, got {len(zones)}"
    assert (
        "W2ABC" in zones[0].name
    ), f"Expected W2ABC in zone name, got: {zones[0].name}"

    print("✅ LocationClusterZoneGenerator test passed!")


def test_distance_banded():
    """Test the DistanceBandedZoneGenerator."""
    print("\nTesting DistanceBandedZoneGenerator...")

    # Create test channels at different distances from NYC
    channels = [
        create_test_channel(
            "NYC Local", 40.7128, -74.0060, "W2ABC", "New York", 1
        ),  # 0km
        create_test_channel(
            "NJ Nearby", 40.0583, -74.4057, "W2DEF", "New Jersey", 2
        ),  # ~80km
        create_test_channel(
            "Philly Regional", 39.9526, -75.1652, "W3GHI", "Philadelphia", 3
        ),  # ~150km
        create_test_channel(
            "DC Far", 38.9072, -77.0369, "W4JKL", "Washington", 4
        ),  # ~360km
    ]

    # Define distance bands
    distance_bands = [
        ("Local", 0, 100),  # 0-100km
        ("Regional", 100, 200),  # 100-200km
        ("Distant", 200, 500),  # 200-500km
    ]

    generator = DistanceBandedZoneGenerator(
        channels=channels,
        reference_lat=40.7128,  # NYC
        reference_lon=-74.0060,
        distance_bands=distance_bands,
    )

    seq = Sequence()
    zones = generator.zones(seq)

    print(f"Generated {len(zones)} zones:")
    for zone in zones:
        print(f"  - {zone.name}: {len(zone.channels)} channels")

    # Should create 3 zones for the 4 channels
    assert len(zones) == 3, f"Expected 3 zones, got {len(zones)}"

    zone_names = [zone.name for zone in zones]
    assert any("Local" in name for name in zone_names), "Missing Local zone"
    assert any("Regional" in name for name in zone_names), "Missing Regional zone"
    assert any("Distant" in name for name in zone_names), "Missing Distant zone"

    print("✅ DistanceBandedZoneGenerator test passed!")


def test_min_cluster_size():
    """Test that clusters below minimum size are excluded."""
    print("\nTesting minimum cluster size filter...")

    # Create channels where no cluster meets the minimum size
    channels = [
        create_test_channel("W2ABC NYC", 40.7128, -74.0060, "W2ABC", "New York", 1),
        create_test_channel(
            "W6XYZ SF", 37.7749, -122.4194, "W6XYZ", "San Francisco", 2
        ),
        create_test_channel("W4JKL DC", 38.9072, -77.0369, "W4JKL", "Washington", 3),
    ]

    generator = LocationClusterZoneGenerator(
        channels=channels,
        max_distance_km=200.0,  # Large enough to cluster all
        min_repeaters_per_zone=5,  # Higher than any cluster can achieve
        zone_naming="representative",
    )

    seq = Sequence()
    zones = generator.zones(seq)

    print(f"Generated {len(zones)} zones (should be 0 due to min_repeaters=5)")

    assert len(zones) == 0, f"Expected 0 zones, got {len(zones)}"

    print("✅ Minimum cluster size filter test passed!")


if __name__ == "__main__":
    print("Testing Location-Based Zone Generators\n")

    try:
        test_location_clustering()
        test_distance_banded()
        test_min_cluster_size()

        print(
            "\n🎉 All tests passed! Location-based zone generators are working correctly."
        )

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
