#!/usr/bin/env python3
"""
Test script to demonstrate the DistanceFilter functionality.
"""

from codeplug.models import DigitalChannel, TxPower, DigitalAnytoneExtensions
from codeplug.generators import Sequence
from codeplug.filters import DistanceFilter, FilterChain, haversine_distance


class MockChannelGenerator:
    """Mock channel generator for testing purposes."""

    def __init__(self):
        self._channels = None

    def channels(self, sequence):
        if self._channels is None:
            self._channels = self._create_test_channels(sequence)
        return self._channels

    def _create_test_channels(self, sequence):
        """Create test channels at various locations."""
        test_channels = []

        # Test data: (name, lat, lng, expected_distance_from_NYC)
        test_locations = [
            ("NYC - Times Square", 40.7589, -73.9851, 0.0),  # Very close to NYC center
            ("NYC - Central Park", 40.7829, -73.9654, 3.2),  # About 3km from NYC center
            ("Brooklyn Bridge", 40.7061, -73.9969, 2.8),  # About 2.8km from NYC center
            ("Newark, NJ", 40.7357, -74.1724, 14.2),  # About 14km from NYC
            ("Philadelphia", 39.9526, -75.1652, 129.7),  # About 130km from NYC
            ("Boston", 42.3601, -71.0589, 306.8),  # About 307km from NYC
            ("No Coordinates", None, None, None),  # Channel without coordinates
        ]

        anytone_ext = DigitalAnytoneExtensions(
            talkaround=None,
            frequencyCorrection=None,
            handsFree=None,
            fmAPRSFrequency=None,
            callConfirm=False,
            sms=True,
            smsConfirm=True,
            dataACK=None,
            simplexTDMA=None,
            adaptiveTDMA=None,
            loneWorker=None,
            throughMode=None,
        )

        for name, lat, lng, expected_dist in test_locations:
            test_channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=name,
                    rx_freq=145.500,
                    tx_freq=145.500,
                    tx_power=TxPower.High,
                    scanlist_id=None,
                    tot=None,
                    rx_only=False,
                    admit_crit="Always",
                    color=1,
                    slot=2,
                    rx_grouplist_id=None,
                    tx_contact_id=None,
                    aprs=None,
                    anytone=anytone_ext,
                    _lat=lat,
                    _lng=lng,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )

        return test_channels


def test_distance_calculation():
    """Test the haversine distance calculation function."""
    print("Testing distance calculation...")

    # NYC coordinates
    nyc_lat, nyc_lng = 40.7128, -74.0060

    # Test known distances
    test_cases = [
        # (lat, lng, expected_distance_km, description)
        (40.7128, -74.0060, 0.0, "Same point (NYC to NYC)"),
        (40.7589, -73.9851, 3.2, "Times Square to NYC center"),
        (39.9526, -75.1652, 129.7, "Philadelphia to NYC"),
        (42.3601, -71.0589, 306.8, "Boston to NYC"),
    ]

    for lat, lng, expected, description in test_cases:
        calculated = haversine_distance(nyc_lat, nyc_lng, lat, lng)
        print(f"  {description}: {calculated:.1f}km (expected ~{expected:.1f}km)")

    print()


def test_distance_filter():
    """Test the DistanceFilter with various distance thresholds."""
    print("Testing DistanceFilter...")

    # NYC coordinates (approximately)
    nyc_lat, nyc_lng = 40.7128, -74.0060

    # Create mock generator and get all channels
    mock_generator = MockChannelGenerator()
    sequence = Sequence()
    all_channels = mock_generator.channels(sequence)

    # Test different distance thresholds
    test_distances = [5, 20, 150, 500]

    for max_distance in test_distances:
        print(f"\n--- Testing with max distance: {max_distance}km ---")

        # Create distance filter
        distance_filter = DistanceFilter(
            reference_lat=nyc_lat,
            reference_lng=nyc_lng,
            max_distance_km=max_distance,
            include_items_without_coordinates=False,
        )

        # Apply filter to channels
        filter_chain = FilterChain([distance_filter])
        filtered_channels = filter_chain.filter_items(all_channels)

        print(f"Channels within {max_distance}km of NYC:")
        for channel in filtered_channels:
            if channel._lat is not None and channel._lng is not None:
                distance = haversine_distance(
                    nyc_lat, nyc_lng, float(channel._lat), float(channel._lng)
                )
                print(f"  - {channel.name}: {distance:.1f}km")
            else:
                print(f"  - {channel.name}: No coordinates")

    # Test including channels without coordinates
    print(f"\n--- Testing with coordinates inclusion enabled ---")
    mock_generator = MockChannelGenerator()
    sequence = Sequence()
    all_channels = mock_generator.channels(sequence)

    distance_filter_with_no_coords = DistanceFilter(
        reference_lat=nyc_lat,
        reference_lng=nyc_lng,
        max_distance_km=50,
        include_items_without_coordinates=True,
    )

    filter_chain = FilterChain([distance_filter_with_no_coords])
    filtered_channels = filter_chain.filter_items(all_channels)
    print(f"Channels within 50km (including those without coordinates):")
    for channel in filtered_channels:
        if channel._lat is not None and channel._lng is not None:
            distance = haversine_distance(
                nyc_lat, nyc_lng, float(channel._lat), float(channel._lng)
            )
            print(f"  - {channel.name}: {distance:.1f}km")
        else:
            print(f"  - {channel.name}: No coordinates (included)")


def main():
    """Main test function."""
    print("Distance Filter Test Suite")
    print("=" * 40)

    test_distance_calculation()
    test_distance_filter()

    print("\n" + "=" * 40)
    print("All tests completed!")


if __name__ == "__main__":
    main()
