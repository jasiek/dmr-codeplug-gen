import re
from collections import defaultdict
from typing import List, Optional, Pattern
from models import ScanList, ScanListID, ChannelID, DigitalChannel, AnalogChannel
from generators import Sequence


class ScanListGenerator:
    """Base generator for scan lists."""

    def __init__(self, name: str, channels: List):
        self.name = name
        self.channels = channels

    def scanlists(self, seq: Sequence) -> List[ScanList]:
        """Generate a single scan list containing the provided channels."""
        if not self.channels:
            return []

        channel_ids = [ch.internal_id for ch in self.channels]
        scanlist = ScanList(
            internal_id=seq.next(), name=self.name, channels=channel_ids
        )
        return [scanlist]


class CallsignPrefixAnalogScanListGenerator:
    """Generator that creates analog scan lists grouped by callsign prefix."""

    DEFAULT_PREFIX_REGEX = r"^([A-Z]{2}[0-9])"

    def __init__(
        self,
        analog_channels: List[AnalogChannel],
        prefix_regex: Optional[str] = None,
        suffix: str = "Analog",
    ):
        self.analog_channels = [
            chan for chan in analog_channels if isinstance(chan, AnalogChannel)
        ]
        self.prefix_pattern: Pattern = re.compile(
            prefix_regex or self.DEFAULT_PREFIX_REGEX
        )
        self.suffix = suffix

    def scanlists(self, seq: Sequence) -> List[ScanList]:
        grouped = defaultdict(list)
        for chan in self.analog_channels:
            prefix = self.callsign_prefix(chan._rpt_callsign)
            if not prefix:
                continue
            grouped[prefix].append(chan)

        output = []
        for prefix in sorted(grouped.keys()):
            channels = sorted(grouped[prefix], key=lambda ch: ch.name)
            channel_ids = [ch.internal_id for ch in channels]
            name = f"{prefix} {self.suffix}"
            output.append(
                ScanList(internal_id=seq.next(), name=name, channels=channel_ids)
            )

        return output[:250]

    def callsign_prefix(self, callsign: Optional[str]) -> Optional[str]:
        if not callsign:
            return None
        if match := self.prefix_pattern.match(callsign):
            return match.group(1)
        return callsign[:3]


class CallsignPrefixDigitalScanListGenerator:
    """Generator that creates digital scan lists grouped by callsign prefix."""

    DEFAULT_PREFIX_REGEX = CallsignPrefixAnalogScanListGenerator.DEFAULT_PREFIX_REGEX

    def __init__(
        self,
        digital_channels: List[DigitalChannel],
        prefix_regex: Optional[str] = None,
        suffix: str = "Digital",
    ):
        self.digital_channels = [
            chan for chan in digital_channels if isinstance(chan, DigitalChannel)
        ]
        self.prefix_pattern: Pattern = re.compile(
            prefix_regex or self.DEFAULT_PREFIX_REGEX
        )
        self.suffix = suffix

    def scanlists(self, seq: Sequence) -> List[ScanList]:
        grouped = defaultdict(list)
        for chan in self.digital_channels:
            prefix = self.callsign_prefix(chan._rpt_callsign)
            if not prefix:
                continue
            grouped[prefix].append(chan)

        output = []
        for prefix in sorted(grouped.keys()):
            channels = sorted(grouped[prefix], key=lambda ch: ch.name)
            channel_ids = [ch.internal_id for ch in channels]
            name = f"{prefix} {self.suffix}"
            output.append(
                ScanList(internal_id=seq.next(), name=name, channels=channel_ids)
            )

        return output[:250]

    def callsign_prefix(self, callsign: Optional[str]) -> Optional[str]:
        if not callsign:
            return None
        if match := self.prefix_pattern.match(callsign):
            return match.group(1)
        return callsign[:3]


class StateScanListGenerator:
    """Generator for creating separate analog and digital scan lists per state."""

    def __init__(
        self,
        state_code: str,
        analog_channels: List[AnalogChannel],
        digital_channels: List[DigitalChannel],
    ):
        self.state_code = state_code
        self.analog_channels = analog_channels
        self.digital_channels = digital_channels

    def scanlists(self, seq: Sequence) -> List[ScanList]:
        """Generate analog and digital scan lists for a state."""
        scanlists = []

        # Create analog scan list if there are analog channels
        if self.analog_channels:
            analog_channel_ids = [ch.internal_id for ch in self.analog_channels]
            analog_scanlist = ScanList(
                internal_id=seq.next(),
                name=f"{self.state_code} Analog",
                channels=analog_channel_ids,
            )
            scanlists.append(analog_scanlist)

        # Create digital scan list if there are digital channels
        if self.digital_channels:
            digital_channel_ids = [ch.internal_id for ch in self.digital_channels]
            digital_scanlist = ScanList(
                internal_id=seq.next(),
                name=f"{self.state_code} Digital",
                channels=digital_channel_ids,
            )
            scanlists.append(digital_scanlist)

        return scanlists
