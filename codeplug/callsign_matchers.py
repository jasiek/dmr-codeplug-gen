"""
Callsign matching system for filtering repeaters by geographic region.
"""

import re
from abc import ABC, abstractmethod


class CallsignMatcher(ABC):
    """Abstract base class for callsign matching."""

    @abstractmethod
    def matches(self, callsign: str) -> bool:
        """Return True if the callsign matches the criteria."""
        pass


class PrefixMatcher(CallsignMatcher):
    """Simple prefix-based matcher (backwards compatibility)."""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def matches(self, callsign: str) -> bool:
        return callsign.startswith(self.prefix)


class RegexMatcher(CallsignMatcher):
    """Regex-based callsign matcher."""

    def __init__(self, pattern: str, flags: int = re.IGNORECASE):
        self.pattern = re.compile(pattern, flags)

    def matches(self, callsign: str) -> bool:
        return bool(self.pattern.match(callsign))


class NYNJCallsignMatcher(CallsignMatcher):
    """Matcher for New York and New Jersey amateur radio callsigns.

    NY and NJ callsigns follow FCC regional patterns:
    - New York: Call sign district 2 (K2, N2, W2, KC2, KD2, etc.)
    - New Jersey: Call sign district 2 (K2, N2, W2, KC2, KD2, etc.)

    Both states are in FCC call sign district 2, so we match:
    - 1x2 format: K2XXX, N2XXX, W2XXX
    - 2x1 format: KC2X, KD2X, etc.
    - 2x2 format: KC2XX, KD2XX, etc.
    - 2x3 format: KC2XXX, KD2XXX, etc.

    Note: A-prefix callsigns are restricted to AA-AL range for US stations.
    This prevents matching foreign callsigns like AP2HD (Pakistan).
    """

    def __init__(self):
        # Pattern for call district 2 (NY/NJ region)
        # Matches: K2XXX, N2XXX, W2XXX, KC2X, KD2XX, KC2XXX, AA2-AL2 formats
        # K, N, W can be followed by any letter; A can only be followed by A-L
        self.pattern = re.compile(
            r"^(K[A-Z]?2|N[A-Z]?2|W[A-Z]?2|A[A-L]2)[A-Z]{1,3}$", re.IGNORECASE
        )

    def matches(self, callsign: str) -> bool:
        return bool(self.pattern.match(callsign.strip()))


class MultiMatcher(CallsignMatcher):
    """Matcher that combines multiple matchers with OR logic."""

    def __init__(self, *matchers: CallsignMatcher):
        self.matchers = matchers

    def matches(self, callsign: str) -> bool:
        return any(matcher.matches(callsign) for matcher in self.matchers)


class AllMatcher(CallsignMatcher):
    """Matcher that matches all callsigns (no filtering)."""

    def matches(self, callsign: str) -> bool:
        return True
