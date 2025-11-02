from typing import List
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
