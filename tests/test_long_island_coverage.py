import os
import sys
from types import SimpleNamespace

import pytest
from lxml import etree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codeplug"))

from datasources.repeaterbook import (  # noqa: E402
    RepeaterBookAPI,
    merge_rxf,
    qth_state_county,
    split_rxf,
)
from filters import AnyFilter, DistanceFilter, RegionFilter  # noqa: E402
from recipes.nyc import NYC_LAT, NYC_LNG, Recipe, analog_region  # noqa: E402


def at(lat, lng):
    return SimpleNamespace(_lat=lat, _lng=lng)


@pytest.fixture
def nyc_filter():
    recipe = Recipe.__new__(Recipe)
    recipe.reference_lat = NYC_LAT
    recipe.reference_lng = NYC_LNG
    recipe.max_distance_km = 100.0
    return recipe.location_filter()


@pytest.mark.parametrize(
    "place,lat,lng",
    [
        ("Manhattan", 40.7128, -74.0060),
        ("Hempstead", 40.7062, -73.6187),
        ("Riverhead", 40.9170, -72.6620),
        ("Southampton", 40.8843, -72.3895),
        ("Montauk", 41.0359, -71.9545),
        ("Montauk Point", 41.0710, -71.8570),
        ("Orient Point", 41.1580, -72.2440),
        ("Bridgeport", 41.1865, -73.1952),
    ],
)
def test_included(nyc_filter, place, lat, lng):
    assert nyc_filter.should_include(at(lat, lng))[0], place


@pytest.mark.parametrize(
    "place,lat,lng",
    [
        ("New Haven", 41.3083, -72.9279),
        ("Old Saybrook", 41.2918, -72.3762),
        ("New London", 41.3557, -72.0995),
        ("Block Island", 41.1720, -71.5578),
        ("Philadelphia", 39.9526, -75.1652),
    ],
)
def test_excluded(nyc_filter, place, lat, lng):
    assert not nyc_filter.should_include(at(lat, lng))[0], place


def test_no_gap_along_long_island():
    """Every point along the island's spine is covered by circle or box."""
    nyc = DistanceFilter(NYC_LAT, NYC_LNG, 100.0)
    box = RegionFilter(min_lat=40.55, max_lat=41.2, min_lng=-73.2, max_lng=-71.8)
    lng = -73.75
    while lng < -71.9:
        for lat in (40.65, 40.8, 40.95):
            point = at(lat, lng)
            assert nyc.should_include(point)[0] or box.should_include(point)[0], (
                lat,
                lng,
            )
        lng += 0.01


def test_any_filter_reasons_when_all_fail():
    f = AnyFilter([RegionFilter(0, 1, 0, 1), RegionFilter(2, 3, 2, 3)])
    ok, reason = f.should_include(at(5, 5))
    assert not ok
    assert reason.count("outside region bounds") == 2


def test_any_filter_passes_if_one_passes():
    f = AnyFilter([RegionFilter(0, 1, 0, 1), RegionFilter(2, 3, 2, 3)])
    assert f.should_include(at(2.5, 2.5)) == (True, "")


def rxf(*ids):
    nodes = "".join(f"<repeater><id>{i}</id><qra>K{i}</qra></repeater>" for i in ids)
    return etree.fromstring(f"<rxf><repeaters>{nodes}</repeaters></rxf>")


def test_merge_rxf_dedupes_by_id():
    merged = merge_rxf(rxf(1, 2), rxf(2, 3))
    ids = [n.findtext("id") for n in merged.findall("repeaters/repeater")]
    assert ids == ["1", "2", "3"]


def test_merge_rxf_keeps_same_id_in_different_states():
    """RepeaterBook ids are per state: NY #22 and NJ #22 are distinct."""
    ny = etree.fromstring(
        "<rxf><repeaters>"
        "<repeater><id>22</id><qth>Brooklyn, New York, Kings</qth></repeater>"
        "<repeater><id>22</id><qth>Newark, New Jersey, Essex</qth></repeater>"
        "</repeaters></rxf>"
    )
    again = etree.fromstring(
        "<rxf><repeaters>"
        "<repeater><id>22</id><qth>Brooklyn, New York, Kings</qth></repeater>"
        "</repeaters></rxf>"
    )
    merged = merge_rxf(ny, again)
    qths = [n.findtext("qth") for n in merged.findall("repeaters/repeater")]
    assert qths == ["Brooklyn, New York, Kings", "Newark, New Jersey, Essex"]


def test_merge_rxf_leaves_sources_untouched():
    a = rxf(1)
    merge_rxf(a)
    assert len(a.findall("repeaters/repeater")) == 1


def listing(qth, id=1):
    return etree.fromstring(f"<repeater><id>{id}</id><qth>{qth}</qth></repeater>")


@pytest.mark.parametrize(
    "qth,expected",
    [
        ("Hauppauge, New York, Suffolk", ("New York", "Suffolk")),
        ("Manhattan, New York", ("New York", None)),
        ("Mt Olive, Twp, New Jersey, Morris", ("New Jersey", "Morris")),
        ("Somewhere", (None, None)),
        ("", (None, None)),
    ],
)
def test_qth_state_county(qth, expected):
    assert qth_state_county(listing(qth)) == expected


@pytest.mark.parametrize(
    "qth,region",
    [
        ("Hauppauge, New York, Suffolk", "LI"),
        ("Mineola, New York, Nassau", "LI"),
        ("Jamaica, New York, Queens", "NYC"),
        ("Manhattan, New York", "NYC"),
        ("White Plains, New York, Westchester", "NYC"),
        ("Stamford, Connecticut, Fairfield", "NYC"),
        ("Mt Olive, Twp, New Jersey, Morris", "NJ"),
        ("Somerset, New Jersey", "NJ"),
    ],
)
def test_analog_region(qth, region):
    assert analog_region(listing(qth)) == region


def test_split_rxf_partitions_every_repeater():
    root = etree.fromstring(
        "<rxf><repeaters>"
        + "".join(
            etree.tostring(listing(q, i)).decode()
            for i, q in enumerate(
                [
                    "A, New York, Suffolk",
                    "B, New Jersey, Bergen",
                    "C, New York, Nassau",
                ]
            )
        )
        + "</repeaters></rxf>"
    )
    parts = split_rxf(root, analog_region)
    ids = {
        k: [n.findtext("id") for n in v.findall("repeaters/repeater")]
        for k, v in parts.items()
    }
    assert ids == {"LI": ["0", "2"], "NJ": ["1"]}
    assert len(root.findall("repeaters/repeater")) == 3


def test_bearer_token_from_environment(monkeypatch):
    monkeypatch.setenv("TURNSTILE_BYPASS_TOKEN", "secret")
    assert RepeaterBookAPI().request_headers() == {"Authorization": "Bearer secret"}
    monkeypatch.delenv("TURNSTILE_BYPASS_TOKEN")
    assert RepeaterBookAPI().request_headers() == {}
