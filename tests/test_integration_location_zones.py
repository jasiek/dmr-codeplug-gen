#!/usr/bin/env python3
"""
Integration test demonstrating location-based zone generators working with the existing system.
This test shows how to integrate the new zone generators with recipes.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "codeplug"))

from generators import Sequence
from generators.location_zones import (
    LocationClusterZoneGenerator,
    DistanceBandedZoneGenerator,
)
from aggregators import ZoneAggregator
from models import DigitalChannel


def create_integration_test_channels():
    """Create test channels that simulate real-world repeater data."""
    channels = []

    # Simulate NY/NJ area repeaters (within 25km of NYC)
    ny_repeaters = [
        DigitalChannel(
            internal_id=1,
            name="W2ABC NYC",
            rx_freq=439.0,
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
            _lat=40.7128,
            _lng=-74.0060,
            _locator=None,
            _rpt_callsign="W2ABC",
            _qth="New York",
        ),
        DigitalChannel(
            internal_id=2,
            name="W2DEF Manhattan",
            rx_freq=442.0,
            tx_freq=442.0,
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
            _lat=40.7505,
            _lng=-73.9934,
            _locator=None,
            _rpt_callsign="W2DEF",
            _qth="Manhattan",
        ),
        DigitalChannel(
            internal_id=3,
            name="W2GHI Brooklyn",
            rx_freq=441.0,
            tx_freq=441.0,
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
            _lat=40.6782,
            _lng=-73.9442,
            _locator=None,
            _rpt_callsign="W2GHI",
            _qth="Brooklyn",
        ),
        DigitalChannel(
            internal_id=4,
            name="W2JKL Newark",
            rx_freq=444.0,
            tx_freq=444.0,
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
            _lat=40.7357,
            _lng=-74.1724,
            _locator=None,
            _rpt_callsign="W2JKL",
            _qth="Newark",
        ),
    ]

    # Simulate distant repeaters (California)
    ca_repeaters = [
        DigitalChannel(
            internal_id=5,
            name="W6XYZ San Francisco",
            rx_freq=440.0,
            tx_freq=440.0,
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
            _lat=37.7749,
            _lng=-122.4194,
            _locator=None,
            _rpt_callsign="W6XYZ",
            _qth="San Francisco",
        ),
        DigitalChannel(
            internal_id=6,
            name="W6MNO Los Angeles",
            rx_freq=442.0,
            tx_freq=442.0,
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
            _lat=34.0522,
            _lng=-118.2437,
            _locator=None,
            _rpt_callsign="W6MNO",
            _qth="Los Angeles",
        ),
    ]

    # Simulate a few more NY area repeaters to create a second cluster
    more_ny_repeaters = [
        DigitalChannel(
            internal_id=7,
            name="W2PQR Yonkers",
            rx_freq=443.0,
            tx_freq=443.0,
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
            _lat=40.9312,
            _lng=-73.8985,
            _locator=None,
            _rpt_callsign="W2PQR",
            _qth="Yonkers",
        ),
        DigitalChannel(
            internal_id=8,
            name="W2STU White Plains",
            rx_freq=444.0,
            tx_freq=444.0,
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
            _lat=41.1220,
            _lng=-73.7949,
            _locator=None,
            _rpt_callsign="W2STU",
            _qth="White Plains",
        ),
    ]

    channels.extend(ny_repeaters + ca_repeaters + more_ny_repeaters)
    return channels


def test_location_clustering_integration():
    """Test location clustering integration with ZoneAggregator."""
    print("Testing Location-Based Zone Clustering Integration...")

    channels = create_integration_test_channels()
    print(f"Created {len(channels)} test channels")

    # Create location cluster generator
    location_gen = LocationClusterZoneGenerator(
        channels=channels,
        max_distance_km=25.0,  # Cluster repeaters within 25km
        min_repeaters_per_zone=2,
        zone_naming="representative",
    )

    # Use with ZoneAggregator (like in real recipes)
    seq = Sequence()
    zones = location_gen.zones(seq)

    print(f"\nGenerated {len(zones)} location-based zones:")
    for zone in zones:
        print(f"  - {zone.name}: {len(zone.channels)} channels")
        for channel_id in zone.channels:
            channel = next(c for c in channels if c.internal_id == channel_id)
            print(f"    • {channel.name} ({channel._rpt_callsign})")

    # Verify we got expected clusters
    assert len(zones) >= 1, f"Expected at least 1 zone, got {len(zones)}"

    # Should have NYC area cluster and possibly others
    nyc_channels = [
        zone
        for zone in zones
        if any("W2ABC" in z or "W2DEF" in z or "W2GHI" in z for z in [zone.name])
    ]
    assert len(nyc_channels) >= 1, "Should have NYC area cluster"

    print("✅ Location clustering integration test passed!")


def test_distance_banded_integration():
    """Test distance banded integration with ZoneAggregator."""
    print("\nTesting Distance-Banded Zone Integration...")

    channels = create_integration_test_channels()

    # Create distance banded generator from NYC
    distance_gen = DistanceBandedZoneGenerator(
        channels=channels,
        reference_lat=40.7128,  # NYC
        reference_lon=-74.0060,
        distance_bands=[
            ("NYC Metro", 0, 50),  # Within 50km
            ("Regional", 50, 150),  # 50-150km
            ("Far", 150, 500),  # 150-500km
            ("Distant", 500, 5000),  # Very far
        ],
    )

    seq = Sequence()
    zones = distance_gen.zones(seq)

    print(f"\nGenerated {len(zones)} distance-banded zones:")
    for zone in zones:
        print(f"  - {zone.name}: {len(zone.channels)} channels")
        for channel_id in zone.channels:
            channel = next(c for c in channels if c.internal_id == channel_id)
            print(f"    • {channel.name} ({channel._rpt_callsign})")

    # Verify we got distance-based zones
    assert len(zones) >= 1, f"Expected at least 1 zone, got {len(zones)}"

    # Should have NYC Metro zone for the closest repeaters
    nyc_metro = [zone for zone in zones if "NYC Metro" in zone.name]
    assert len(nyc_metro) >= 1, "Should have NYC Metro zone for close repeaters"

    print("✅ Distance banded integration test passed!")


def test_mixed_zone_generation():
    """Test using multiple zone generators together in ZoneAggregator."""
    print("\nTesting Mixed Zone Generation (Location + Traditional)...")

    channels = create_integration_test_channels()

    # Create location-based zones
    location_gen = LocationClusterZoneGenerator(
        channels=channels,
        max_distance_km=50.0,
        min_repeaters_per_zone=3,
        zone_naming="representative",
    )

    # Simulate traditional callsign-based zones (simplified)
    class MockCallsignGen:
        def zones(self, seq):
            # Group by state prefix
            ny_channels = [
                c
                for c in channels
                if c._rpt_callsign and c._rpt_callsign.startswith("W2")
            ]
            ca_channels = [
                c
                for c in channels
                if c._rpt_callsign and c._rpt_callsign.startswith("W6")
            ]

            from models import Zone

            zones = []
            if ny_channels:
                zones.append(
                    Zone(
                        internal_id=seq.next(),
                        name="W2 Digital",
                        channels=[c.internal_id for c in ny_channels],
                    )
                )
            if ca_channels:
                zones.append(
                    Zone(
                        internal_id=seq.next(),
                        name="W6 Digital",
                        channels=[c.internal_id for c in ca_channels],
                    )
                )
            return zones

    traditional_gen = MockCallsignGen()

    # Combine in ZoneAggregator (simulating real recipe usage)
    zone_agg = ZoneAggregator(location_gen, traditional_gen)
    seq = Sequence()
    all_zones = zone_agg.zones(seq)

    print(f"\nGenerated {len(all_zones)} total zones:")
    location_zones = []
    traditional_zones = []

    for zone in all_zones:
        if "W2" in zone.name and "Digital" in zone.name:
            traditional_zones.append(zone)
        else:
            location_zones.append(zone)
        print(f"  - {zone.name}: {len(zone.channels)} channels")

    print(f"\nLocation-based zones: {len(location_zones)}")
    print(f"Traditional zones: {len(traditional_zones)}")

    assert (
        len(all_zones) >= 2
    ), f"Expected at least 2 zones (location + traditional), got {len(all_zones)}"

    print("✅ Mixed zone generation test passed!")


def test_recipe_simulation():
    """Simulate how this would work in a real recipe."""
    print("\nSimulating Recipe Integration...")

    channels = create_integration_test_channels()

    # This simulates what a recipe's prepare_zones() method might look like
    def simulate_prepare_zones(recipe_location):
        """Simulate a recipe's zone preparation with location-based clustering."""
        seq = Sequence()

        # Create location-based zones from analog channels (simulated with our test channels)
        location_cluster_gen = LocationClusterZoneGenerator(
            channels=channels,
            max_distance_km=30.0,
            min_repeaters_per_zone=2,
            zone_naming="representative",
        )

        # Create distance-banded zones from same channels
        distance_banded_gen = DistanceBandedZoneGenerator(
            channels=channels,
            reference_lat=recipe_location[0],
            reference_lon=recipe_location[1],
            distance_bands=[
                ("Local", 0, 100),
                ("Regional", 100, 300),
                ("Far", 300, 1000),
            ],
        )

        # Use both generators in ZoneAggregator
        zones = ZoneAggregator(location_cluster_gen, distance_banded_gen).zones(seq)

        return zones

    # Test with different reference locations
    locations = [
        (40.7128, -74.0060),  # NYC
        (34.0522, -118.2437),  # Los Angeles
        (41.8781, -87.6298),  # Chicago
    ]

    for i, location in enumerate(locations, 1):
        print(f"\nTest {i}: Reference location ({location[0]:.2f}, {location[1]:.2f})")
        zones = simulate_prepare_zones(location)
        print(f"Generated {len(zones)} zones:")
        for zone in zones[:3]:  # Show first 3 zones
            print(f"  - {zone.name}: {len(zone.channels)} channels")
        if len(zones) > 3:
            print(f"  ... and {len(zones) - 3} more zones")

    print("✅ Recipe simulation test passed!")


if __name__ == "__main__":
    print("Testing Location-Based Zone Generator Integration\n")

    try:
        test_location_clustering_integration()
        test_distance_banded_integration()
        test_mixed_zone_generation()
        test_recipe_simulation()

        print("\n🎉 All integration tests passed!")
        print(
            "\nThe location-based zone generators are fully integrated with the existing system:"
        )
        print("✅ Compatible with ZoneAggregator")
        print("✅ Work with existing recipe patterns")
        print("✅ Support mixed zone generation")
        print("✅ Can be used alongside traditional zone generators")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
