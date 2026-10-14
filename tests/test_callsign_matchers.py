import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codeplug"))

from callsign_matchers import NYNJCallsignMatcher, base_callsign  # noqa: E402


class TestBaseCallsign:
    def test_strips_city_suffix(self):
        assert base_callsign("W2NJR Sprgfld NJ") == "W2NJR"

    def test_strips_dash_suffix(self):
        assert base_callsign("W2RCR-BAYONNENJ") == "W2RCR"

    def test_uppercases(self):
        assert base_callsign(" w2brw ") == "W2BRW"


class TestNYNJMatcherWithDecoratedCallsigns:
    def test_matches_callsign_with_city(self):
        assert NYNJCallsignMatcher().matches("W2SOM Brdgwtr NJ")

    def test_matches_callsign_with_dash_suffix(self):
        assert NYNJCallsignMatcher().matches("W2RCR-ELIZABETH")

    def test_still_rejects_other_districts(self):
        assert not NYNJCallsignMatcher().matches("W6ABC Somewhere")
