from enum import Enum
from typing import List, Optional, NewType, Union, Literal
from dataclasses import dataclass

# type definitions

InternalID = NewType("InternalID", int)
DMRID = NewType("DMRID", int)

ContactID = InternalID
GroupListID = InternalID
ChannelID = InternalID
ScanListID = InternalID

Slot = Union[Literal[1], Literal[2]]
Latitude = Optional[float]
Longitude = Optional[float]
Locator = Optional[str]


class TxPower(Enum):
    Min = "Min"
    Low = "Low"
    Mid = "Mid"
    High = "High"
    Max = "Max"


# model definitions


@dataclass
class Contact:
    internal_id: ContactID
    name: str
    calling_id: DMRID


@dataclass
class GroupList:
    internal_id: GroupListID
    name: str
    contact_ids: List[ContactID]


@dataclass
class DigitalChannel:
    internal_id: ChannelID
    name: str
    rx_freq: float
    tx_freq: float
    tx_power: TxPower
    scanlist_id: Optional[ScanListID]
    tot: str  # literal
    rx_only: str  # bool
    admit_crit: str  # literal
    color: int
    slot: Slot
    rx_grouplist_id: Optional[GroupListID]
    tx_contact_id: Optional[ContactID]
    lat: Latitude
    lng: Longitude
    locator: Locator


def is_hotspot(chan):
    return chan.name.startswith("HS")


@dataclass
class AnalogChannel:
    internal_id: ChannelID
    name: str
    rx_freq: float
    tx_freq: float
    tx_power: TxPower
    scanlist_id: Optional[ScanListID]
    tot: str  # literal
    rx_only: str  # bool
    admit_crit: str  # literal
    squelch: str  # Literal
    rx_tone: float  # optional float
    tx_tone: float  # optional float
    width: float  # enum
    lat: Latitude
    lng: Longitude
    locator: Locator


@dataclass
class Zone:
    internal_id: int
    name: str
    channels: List[ChannelID]
