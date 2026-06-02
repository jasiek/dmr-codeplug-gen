#!/usr/bin/env python3
"""
Tests for the debug mode of FilterChain.filter_items, exercised through the
DistanceFilter, BandFilter and RegionFilter filters.
"""

from codeplug.filters import (
    DistanceFilter,
    RegionFilter,
    BandFilter,
    FilterChain,
)


def make_channel(**attrs):
    """Build a lightweight mock channel object from keyword attributes."""
    return type("Channel", (), attrs)()


def test_distance_filter_debug_output(capsys):
    channels = [
        make_channel(name="Close Channel", _lat=37.5, _lng=-122.2, internal_id=1),
        make_channel(name="Far Channel", _lat=38.0, _lng=-122.0, internal_id=2),
        make_channel(name="No Coords Channel", _lat=None, _lng=None, internal_id=3),
    ]

    distance_filter = DistanceFilter(
        reference_lat=37.4852,
        reference_lng=-122.2364,
        max_distance_km=50.0,
        include_items_without_coordinates=False,
    )
    filter_chain = FilterChain([distance_filter])
    filtered = filter_chain.filter_items(channels, debug=True)

    # Only the close channel survives; far and no-coords are dropped.
    assert [c.name for c in filtered] == ["Close Channel"]

    out = capsys.readouterr().out
    assert "Far Channel" in out
    assert "No Coords Channel" in out
    assert "Close Channel" not in out


def test_band_filter_debug_output(capsys):
    channels = [
        make_channel(name="2m Channel", rx_freq=145.0, internal_id=1),
        make_channel(name="70cm Channel", rx_freq=433.0, internal_id=2),
        make_channel(name="Out of band Channel", rx_freq=150.0, internal_id=3),
    ]

    band_filter = BandFilter(frequency_ranges=[(144.0, 148.0)])
    filter_chain = FilterChain([band_filter])
    filtered = filter_chain.filter_items(channels, debug=True)

    assert [c.name for c in filtered] == ["2m Channel"]

    out = capsys.readouterr().out
    assert "70cm Channel" in out
    assert "Out of band Channel" in out
    assert "2m Channel" not in out


def test_region_filter_debug_output(capsys):
    channels = [
        make_channel(name="Inside Region", _lat=37.5, _lng=-122.5, internal_id=1),
        make_channel(name="Outside Region", _lat=39.0, _lng=-121.0, internal_id=2),
    ]

    region_filter = RegionFilter(
        min_lat=37.0, max_lat=38.0, min_lng=-123.0, max_lng=-122.0
    )
    filter_chain = FilterChain([region_filter])
    filtered = filter_chain.filter_items(channels, debug=True)

    assert [c.name for c in filtered] == ["Inside Region"]

    out = capsys.readouterr().out
    assert "Outside Region" in out
    assert "Inside Region" not in out


def test_debug_disabled_produces_no_output(capsys):
    channels = [
        make_channel(name="2m Channel", rx_freq=145.0, internal_id=1),
        make_channel(name="Out of band Channel", rx_freq=150.0, internal_id=2),
    ]

    filter_chain = FilterChain([BandFilter(frequency_ranges=[(144.0, 148.0)])])
    filtered = filter_chain.filter_items(channels, debug=False)

    assert [c.name for c in filtered] == ["2m Channel"]
    assert capsys.readouterr().out == ""
