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


class CTCallsignMatcher(CallsignMatcher):
    """Matcher for Connecticut amateur radio callsigns.

    Connecticut callsigns follow FCC regional patterns:
    - Connecticut: Call sign district 1 (K1, N1, W1, KC1, KD1, etc.)

    Matches:
    - 1x2 format: K1XXX, N1XXX, W1XXX
    - 2x1 format: KC1X, KD1X, etc.
    - 2x2 format: KC1XX, KD1XX, etc.
    - 2x3 format: KC1XXX, KD1XXX, etc.

    Note: A-prefix callsigns are restricted to AA-AL range for US stations.
    Call district 1 covers all of New England (CT, MA, ME, NH, RI, VT).
    """

    def __init__(self):
        # Pattern for call district 1 (New England region including CT)
        # Matches: K1XXX, N1XXX, W1XXX, KC1X, KD1XX, KC1XXX, AA1-AL1 formats
        self.pattern = re.compile(
            r"^(K[A-Z]?1|N[A-Z]?1|W[A-Z]?1|A[A-L]1)[A-Z]{1,3}$", re.IGNORECASE
        )

    def matches(self, callsign: str) -> bool:
        return bool(self.pattern.match(callsign.strip()))


class CACallsignMatcher(CallsignMatcher):
    """Matcher for California amateur radio callsigns.

    California callsigns follow FCC regional patterns:
    - California: Call sign district 6 (K6, N6, W6, KC6, KD6, etc.)

    Matches:
    - 1x2 format: K6XXX, N6XXX, W6XXX
    - 2x1 format: KC6X, KD6X, etc.
    - 2x2 format: KC6XX, KD6XX, etc.
    - 2x3 format: KC6XXX, KD6XXX, etc.

    Note: A-prefix callsigns are restricted to AA-AL range for US stations.
    """

    def __init__(self):
        # Pattern for call district 6 (CA region)
        # Matches: K6XXX, N6XXX, W6XXX, KC6X, KD6XX, KC6XXX, AA6-AL6 formats
        self.pattern = re.compile(
            r"^(K[A-Z]?6|N[A-Z]?6|W[A-Z]?6|A[A-L]6)[A-Z]{1,3}$", re.IGNORECASE
        )

    def matches(self, callsign: str) -> bool:
        return bool(self.pattern.match(callsign.strip()))


class NMCallsignMatcher(CallsignMatcher):
    """Matcher for New Mexico amateur radio callsigns.

    New Mexico callsigns follow FCC regional patterns:
    - New Mexico: Call sign district 5 (K5, N5, W5, KC5, KD5, etc.)

    Matches:
    - 1x2 format: K5XXX, N5XXX, W5XXX
    - 2x1 format: KC5X, KD5X, etc.
    - 2x2 format: KC5XX, KD5XX, etc.
    - 2x3 format: KC5XXX, KD5XXX, etc.

    Note: A-prefix callsigns are restricted to AA-AL range for US stations.
    """

    def __init__(self):
        # Pattern for call district 5 (NM region)
        # Matches: K5XXX, N5XXX, W5XXX, KC5X, KD5XX, KC5XXX, AA5-AL5 formats
        self.pattern = re.compile(
            r"^(K[A-Z]?5|N[A-Z]?5|W[A-Z]?5|A[A-L]5)[A-Z]{1,3}$", re.IGNORECASE
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
