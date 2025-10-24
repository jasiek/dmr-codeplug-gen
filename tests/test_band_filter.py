#!/usr/bin/env python3
"""
Test script to demonstrate the BandFilter functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path to import codeplug modules
sys.path.insert(0, str(Path(__file__).parent.parent / "codeplug"))

from models import AnalogChannel, TxPower, ChannelWidth
from generators import Sequence
from filters import BandFilter


class MockAnalogChannelGenerator:
    """Mock analog channel generator for testing purposes."""

    def __init__(self):
        self._channels = None

    def channels(self, sequence):
        if self._channels is None:
            self._channels = self._create_test_channels(sequence)
        return self._channels

    def _create_test_channels(self, sequence):
        """Create test channels across various frequency bands."""
        test_channels = []

        # Test data: (name, rx_freq, band_name)
        test_frequencies = [
            ("2m Repeater 1", 145.230, "2m"),
            ("2m Repeater 2", 146.520, "2m"),
            ("2m Repeater 3", 147.390, "2m"),
            ("6m Repeater", 52.525, "6m"),
            ("1.25m Repeater", 223.500, "1.25m"),
            ("70cm Repeater 1", 442.100, "70cm"),
            ("70cm Repeater 2", 447.000, "70cm"),
            ("70cm Repeater 3", 448.625, "70cm"),
            ("23cm Repeater", 1293.000, "23cm"),
            ("PMR Channel", 446.00625, "PMR"),
        ]

        for name, rx_freq, band_name in test_frequencies:
            test_channels.append(
                AnalogChannel(
                    internal_id=sequence.next(),
                    name=name,
                    rx_freq=rx_freq,
                    tx_freq=rx_freq + 0.600,  # Standard offset
                    tx_power=TxPower.High,
                    scanlist_id=None,
                    tot=None,
                    rx_only=False,
                    admit_crit="Always",
                    squelch=1,
                    rx_tone=None,
                    tx_tone=None,
                    width=ChannelWidth.Narrow,
                    aprs=None,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )

        return test_channels


def test_default_band_filter():
    """Test the BandFilter with default settings (2m and 70cm)."""
    print("Testing BandFilter with default settings (2m and 70cm)...")

    # Create mock generator
    mock_generator = MockAnalogChannelGenerator()

    # Create band filter with defaults
    band_filter = BandFilter(generator=mock_generator)

    # Get filtered channels
    sequence = Sequence()
    filtered_channels = band_filter.channels(sequence)

    print(f"\nChannels in 2m (144-148 MHz) and 70cm (420-450 MHz) bands:")
    print(f"Total filtered channels: {len(filtered_channels)}")
    for channel in filtered_channels:
        print(f"  - {channel.name}: {channel.rx_freq} MHz")

    # Verify we got the expected channels
    expected_count = 7  # 3 from 2m + 3 from 70cm + 1 PMR (which is in 70cm range)
    assert (
        len(filtered_channels) == expected_count
    ), f"Expected {expected_count} channels, got {len(filtered_channels)}"
    print(f"\n✓ Default filter test passed!")


def test_single_band_filter():
    """Test the BandFilter for a single band."""
    print("\n\n--- Testing BandFilter for single bands ---")

    # Test 2m only
    print("\n2m Band Only (144-148 MHz):")
    mock_generator = MockAnalogChannelGenerator()
    band_2m_filter = BandFilter(
        generator=mock_generator, frequency_ranges=[(144.0, 148.0)]
    )

    sequence = Sequence()
    channels_2m = band_2m_filter.channels(sequence)
    print(f"Total channels: {len(channels_2m)}")
    for channel in channels_2m:
        print(f"  - {channel.name}: {channel.rx_freq} MHz")

    assert len(channels_2m) == 3, f"Expected 3 2m channels, got {len(channels_2m)}"

    # Test 70cm only
    print("\n70cm Band Only (420-450 MHz):")
    mock_generator = MockAnalogChannelGenerator()
    band_70cm_filter = BandFilter(
        generator=mock_generator, frequency_ranges=[(420.0, 450.0)]
    )

    sequence = Sequence()
    channels_70cm = band_70cm_filter.channels(sequence)
    print(f"Total channels: {len(channels_70cm)}")
    for channel in channels_70cm:
        print(f"  - {channel.name}: {channel.rx_freq} MHz")

    # Note: PMR channel at 446.00625 MHz is also in the 70cm range (420-450 MHz)
    assert (
        len(channels_70cm) == 4
    ), f"Expected 4 70cm channels (3 repeaters + PMR), got {len(channels_70cm)}"

    print(f"\n✓ Single band filter tests passed!")


def test_multi_band_filter():
    """Test the BandFilter with multiple custom bands."""
    print("\n\n--- Testing BandFilter with multiple custom bands ---")

    # Create mock generator
    mock_generator = MockAnalogChannelGenerator()

    # Filter for 6m, 2m, and 70cm
    multi_band_filter = BandFilter(
        generator=mock_generator,
        frequency_ranges=[
            (50.0, 54.0),  # 6m
            (144.0, 148.0),  # 2m
            (420.0, 450.0),  # 70cm
        ],
    )

    sequence = Sequence()
    filtered_channels = multi_band_filter.channels(sequence)

    print(f"\nChannels in 6m, 2m, and 70cm bands:")
    print(f"Total filtered channels: {len(filtered_channels)}")
    for channel in filtered_channels:
        print(f"  - {channel.name}: {channel.rx_freq} MHz")

    # Should get 1 (6m) + 3 (2m) + 4 (70cm including PMR) = 8 channels
    expected_count = 8
    assert (
        len(filtered_channels) == expected_count
    ), f"Expected {expected_count} channels, got {len(filtered_channels)}"

    print(f"\n✓ Multi-band filter test passed!")


def test_edge_cases():
    """Test edge cases for BandFilter."""
    print("\n\n--- Testing BandFilter edge cases ---")

    # Test with empty frequency ranges
    print("\nTest 1: Empty frequency ranges (should return no channels)")
    mock_generator = MockAnalogChannelGenerator()
    empty_filter = BandFilter(generator=mock_generator, frequency_ranges=[])

    sequence = Sequence()
    filtered_channels = empty_filter.channels(sequence)
    print(f"Channels found: {len(filtered_channels)}")
    assert (
        len(filtered_channels) == 0
    ), "Empty frequency ranges should return no channels"
    print("✓ Passed")

    # Test with boundary values
    print("\nTest 2: Boundary values (exact frequency match)")
    mock_generator = MockAnalogChannelGenerator()
    boundary_filter = BandFilter(
        generator=mock_generator,
        frequency_ranges=[(145.230, 145.230)],  # Exact match for one channel
    )

    sequence = Sequence()
    filtered_channels = boundary_filter.channels(sequence)
    print(f"Channels found: {len(filtered_channels)}")
    assert len(filtered_channels) == 1, "Should match exactly one channel at boundary"
    assert filtered_channels[0].name == "2m Repeater 1"
    print("✓ Passed")

    # Test with overlapping ranges
    print("\nTest 3: Overlapping frequency ranges")
    mock_generator = MockAnalogChannelGenerator()
    overlap_filter = BandFilter(
        generator=mock_generator,
        frequency_ranges=[
            (144.0, 146.0),  # Covers first two 2m repeaters
            (145.0, 148.0),  # Overlaps with above, covers all three 2m repeaters
        ],
    )

    sequence = Sequence()
    filtered_channels = overlap_filter.channels(sequence)
    print(f"Channels found: {len(filtered_channels)}")
    # Should still get 3 unique channels (no duplicates)
    assert (
        len(filtered_channels) == 3
    ), "Overlapping ranges should not create duplicates"
    print("✓ Passed")

    print(f"\n✓ All edge case tests passed!")


def test_filter_caching():
    """Test that filter results are cached properly."""
    print("\n\n--- Testing filter result caching ---")

    mock_generator = MockAnalogChannelGenerator()
    band_filter = BandFilter(generator=mock_generator)

    sequence1 = Sequence()
    channels1 = band_filter.channels(sequence1)

    sequence2 = Sequence()
    channels2 = band_filter.channels(sequence2)

    # Should return the same cached result
    assert channels1 is channels2, "Filter should cache and return same result"
    print("✓ Filter caching test passed!")


def main():
    """Main test function."""
    print("=" * 60)
    print("BandFilter Test Suite")
    print("=" * 60)

    try:
        test_default_band_filter()
        test_single_band_filter()
        test_multi_band_filter()
        test_edge_cases()
        test_filter_caching()

        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
