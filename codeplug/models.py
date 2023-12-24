from enum import Enum
from typing import List, Optional, NewType, Union, Literal
from dataclasses import dataclass

# type definitions

InternalID = NewType("InternalID", int)
DMRID = NewType("DMRID", int)

ContactID = InternalID
GroupListID = InternalID
ChannelID = InternalID

OptionalContactID = Optional[ContactID]


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
    scanlist_id: str  # optional id
    tot: str  # literal
    rx_only: str  # bool
    admit_crit: str  # literal
    color: int
    slot: int  # enum
    rx_grouplist_id: str  # optional id
    tx_contact_id: OptionalContactID
    lat: float  # optional float
    lng: float  # optional float
    locator: str  # optional str


def is_hotspot(chan):
    return chan.name.startswith("HS")


@dataclass
class AnalogChannel:
    internal_id: ChannelID
    name: str
    rx_freq: float
    tx_freq: float
    tx_power: TxPower
    scanlist_id: str  # optional id
    tot: str  # literal
    rx_only: str  # bool
    admit_crit: str  # literal
    squelch: str  # Literal
    rx_tone: float  # optional float
    tx_tone: float  # optional float
    width: float  # enum
    lat: float  # opt float
    lng: float  # opt float
    locator: str  # opt lcoator


@dataclass
class Zone:
    internal_id: int
    name: str
    channels: List[ChannelID]
