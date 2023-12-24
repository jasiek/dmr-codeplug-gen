from typing import List, Optional, NewType
from dataclasses import dataclass

# type definitions

InternalID = NewType("InternalID", int)

ContactID = InternalID
OptionalContactID = Optional[ContactID]

ChannelID = InternalID

# model definitions


@dataclass
class Contact:
    internal_id: ContactID
    name: str
    calling_id: int


@dataclass
class GroupList:
    internal_id: int
    name: str
    contact_ids: List[ContactID]


@dataclass
class DigitalChannel:
    internal_id: ChannelID
    name: str
    rx_freq: float
    tx_freq: float
    tx_power: str  # Literal
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
    tx_power: str  # Literal
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
