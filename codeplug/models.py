from enum import Enum, StrEnum
from typing import List, Optional, NewType, Union, Literal
from dataclasses import dataclass

# type definitions

InternalID = NewType("InternalID", int)
DMRID = NewType("DMRID", int)

ContactID = InternalID
GroupListID = InternalID
ChannelID = InternalID
ScanListID = InternalID
ZoneID = InternalID

Slot = Union[Literal[1], Literal[2]]
Latitude = Optional[float]
Longitude = Optional[float]
Locator = Optional[str]
Squelch = Union[*([Literal[n] for n in range(1, 11)] + [Literal["Open"]])]
TOT = Optional[int]
ColorCode = Union[*[Literal[n] for n in range(1, 65)]]


class DigitalAdmitCriteria(StrEnum):
    Always = "Always"
    Free = "Free"
    ColorCode = "ColorCode"


class AnalogAdmitCriteria(StrEnum):
    Always = "Always"
    Free = "Free"
    Tone = "Tone"


class ContactType(StrEnum):
    GroupCall = "GroupCall"
    PrivateCall = "PrivateCall"
    AllCall = "AllCall"


class TxPower(StrEnum):
    Min = "Min"
    Low = "Low"
    Mid = "Mid"
    High = "High"
    Max = "Max"


class ChannelWidth(StrEnum):
    Narrow = "Narrow"  # 12.5
    Wide = "Wide"  # 25


# model definitions


@dataclass
class Contact:
    internal_id: ContactID
    name: str
    type: ContactType
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
    tot: TOT
    rx_only: bool
    admit_crit: DigitalAdmitCriteria
    color: ColorCode
    slot: Slot
    rx_grouplist_id: Optional[GroupListID]
    tx_contact_id: Optional[ContactID]
    lat: Latitude
    lng: Longitude
    locator: Locator
    _rpt_callsign: Optional[str]  # Optional repeater callsign, for zone grouping


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
    tot: TOT
    rx_only: bool
    admit_crit: AnalogAdmitCriteria
    squelch: Squelch
    rx_tone: Optional[float]
    tx_tone: Optional[float]
    width: ChannelWidth
    lat: Latitude
    lng: Longitude
    locator: Locator
    _rpt_callsign: Optional[str]


@dataclass
class Zone:
    internal_id: ZoneID
    name: str
    channels: List[ChannelID]


@dataclass
class DigitalRoamingChannel:
    internal_id: ChannelID
    name: str
    tx_freq: float
    rx_freq: float
    color: ColorCode
    slot: Slot


@dataclass
class DigitalRoamingZone:
    internal_id: ZoneID
    name: str
    channels: List[ChannelID]
