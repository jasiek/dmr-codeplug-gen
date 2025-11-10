#!/usr/bin/env python3
"""
Simple test to demonstrate the debug mode functionality for filters.
"""
import sys

sys.path.insert(0, "codeplug")

from filters import DistanceFilter, RegionFilter, BandFilter
from models import DigitalChannel


# Create some mock channels with different properties
class MockChannelGenerator:
    def __init__(self, channels):
        self._channels = channels

    def channels(self, sequence):
        return self._channels


# Mock sequence
class MockSequence:
    def __init__(self):
        self.counter = 0

    def next(self):
        self.counter += 1
        return self.counter


# Create test channels
channels = [
    # Channel within 50km
    type(
        "Channel",
        (),
        {
            "name": "Close Channel 1",
            "_lat": 37.5,
            "_lng": -122.2,
            "rx_freq": 145.0,
            "internal_id": 1,
        },
    )(),
    # Channel far away (>50km)
    type(
        "Channel",
        (),
        {
            "name": "Far Channel 1",
            "_lat": 38.0,
            "_lng": -122.0,
            "rx_freq": 146.0,
            "internal_id": 2,
        },
    )(),
    # Channel without coordinates
    type(
        "Channel",
        (),
        {
            "name": "No Coords Channel",
            "_lat": None,
            "_lng": None,
            "rx_freq": 147.0,
            "internal_id": 3,
        },
    )(),
    # Channel with wrong frequency band (out of 2m band)
    type(
        "Channel",
        (),
        {
            "name": "Wrong Band Channel",
            "_lat": 37.48,
            "_lng": -122.23,
            "rx_freq": 433.0,  # 70cm, not 2m
            "internal_id": 4,
        },
    )(),
]

print("=" * 70)
print("Testing DistanceFilter with debug=True")
print("=" * 70)
print(f"\nReference point: 37.4852, -122.2364 (Redwood City, CA)")
print(f"Max distance: 50km\n")

generator = MockChannelGenerator(channels)
distance_filter = DistanceFilter(
    generator,
    reference_lat=37.4852,
    reference_lng=-122.2364,
    max_distance_km=50.0,
    include_channels_without_coordinates=False,
    debug=True,
)

filtered = distance_filter.channels(MockSequence())
print(f"\nResult: {len(filtered)} channels passed the distance filter")

print("\n" + "=" * 70)
print("Testing BandFilter with debug=True")
print("=" * 70)
print(f"\nAllowed frequency ranges: 144.0-148.0 MHz (2m band only)\n")

# Reset to test with all channels again
channels2 = [
    type("Channel", (), {"name": "2m Channel", "rx_freq": 145.0, "internal_id": 1})(),
    type("Channel", (), {"name": "70cm Channel", "rx_freq": 433.0, "internal_id": 2})(),
    type(
        "Channel",
        (),
        {"name": "Out of band Channel", "rx_freq": 150.0, "internal_id": 3},
    )(),
]

generator2 = MockChannelGenerator(channels2)
band_filter = BandFilter(generator2, frequency_ranges=[(144.0, 148.0)], debug=True)

filtered2 = band_filter.channels(MockSequence())
print(f"\nResult: {len(filtered2)} channels passed the band filter")

print("\n" + "=" * 70)
print("Testing RegionFilter with debug=True")
print("=" * 70)
print(f"\nRegion bounds: lat 37.0-38.0, lng -123.0 to -122.0\n")

channels3 = [
    type(
        "Channel",
        (),
        {"name": "Inside Region", "_lat": 37.5, "_lng": -122.5, "internal_id": 1},
    )(),
    type(
        "Channel",
        (),
        {"name": "Outside Region", "_lat": 39.0, "_lng": -121.0, "internal_id": 2},
    )(),
]

generator3 = MockChannelGenerator(channels3)
region_filter = RegionFilter(
    generator3, min_lat=37.0, max_lat=38.0, min_lng=-123.0, max_lng=-122.0, debug=True
)

filtered3 = region_filter.channels(MockSequence())
print(f"\nResult: {len(filtered3)} channels passed the region filter")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
