import json

import maidenhead as mh

from models import DigitalChannel, TxPower, DigitalAnytoneExtensions
from datasources import brandmeister


def channel_label(callsign, tg):
    return f"{tg.calling_id} {tg.name}"


def hotspot_channel_label(contact):
    return f"HS{contact.calling_id} {contact.name}"


DEFAULT_ANYTONE_EXTENSIONS = DigitalAnytoneExtensions(
    talkaround=None,
    frequencyCorrection=None,
    handsFree=None,
    fmAPRSFrequency=None,
    callConfirm=False,
    sms=True,
    smsConfirm=True,
    dataACK=None,
    simplexTDMA=None,
    adaptiveTDMA=None,
    loneWorker=None,
    throughMode=None,
)


class HotspotDigitalChannelGenerator:
    def __init__(
        self,
        talkgroups,
        *,
        aprs_config,
        ts=2,
        f=431.100,
        color=1,
        default_contact_id=None,
    ):
        self.f = f
        self.ts = ts
        self.color = color
        self.talkgroups = talkgroups
        self._channels = []
        self.default_contact = default_contact_id
        self.default_contact_id = default_contact_id
        self.aprs_config = aprs_config

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for slot in [1, 2]:
            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=f"HS TS{slot}",
                    rx_freq=self.f,
                    tx_freq=self.f,
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    color=self.color,
                    slot=slot,
                    rx_grouplist_id="-",
                    tx_contact_id=self.default_contact_id,
                    aprs=self.aprs_config,
                    anytone=DEFAULT_ANYTONE_EXTENSIONS,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )

        for tg in self.talkgroups:
            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=hotspot_channel_label(tg),
                    rx_freq=self.f,
                    tx_freq=self.f,
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    color=self.color,
                    slot=self.ts,
                    rx_grouplist_id="-",
                    tx_contact_id=tg.internal_id,
                    aprs=self.aprs_config,
                    anytone=DEFAULT_ANYTONE_EXTENSIONS,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )


class DigitalChannelGeneratorFromBrandmeister:
    def __init__(
        self,
        power,
        talkgroups,
        *,
        aprs_config,
        callsign_matcher=None,
        default_contact_id=None,
    ):
        self.devices = brandmeister.DeviceDB().devices
        self._channels = []
        self.talkgroups = talkgroups
        self.aprs_config = aprs_config
        self.callsign_matcher = callsign_matcher
        self.default_contact_id = default_contact_id

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        """
        Generate digital channels from Brandmeister repeater database.

        This method processes repeaters from the Brandmeister device database and creates
        DigitalChannel objects for both talkgroup-specific channels and generic timeslot channels.

        Process Overview:
        1. Iterates through all devices in the Brandmeister device database
        2. Filters devices based on callsign_matcher if provided (used to limit channels to specific regions/repeaters)
        3. Skips hotspots (identified by: rx frequency == tx frequency, pep == 1, or statusText == "DMO")
        4. For each repeater device, queries Brandmeister API for static talkgroups configured on that repeater
        5. Creates talkgroup-specific channels for matches between repeater's static TGs and the provided talkgroups list
        6. Creates two generic timeslot channels (TS1 and TS2) for each repeater to allow dynamic talkgroup access

        Channel Creation Details:

        Talkgroup-Specific Channels:
        - Created only when a repeater's static talkgroup matches one from the provided talkgroups list
        - Channel name format: "<repeater_callsign> <tg_calling_id> <tg_name>"
        - Uses the repeater's configured timeslot for that talkgroup
        - Sets tx_contact_id to the specific talkgroup's internal ID for direct access
        - Skips talkgroups on slot 0 (invalid configuration)

        Generic Timeslot Channels:
        - Two channels created per repeater (one for TS1, one for TS2)
        - Channel name format: "<repeater_callsign> TS<slot_number>"
        - No tx_contact_id set (None), allowing user to manually select talkgroup during transmission
        - Provides flexibility for accessing non-static talkgroups

        Channel Configuration:
        - RX frequency: Set to repeater's TX frequency (what the repeater transmits)
        - TX frequency: Set to repeater's RX frequency (what the repeater receives)
        - Color code: Obtained from repeater's configuration
        - Geographic data: Latitude, longitude, maidenhead locator, and QTH extracted from repeater info
        - Handles None values gracefully for missing lat/lng coordinates
        - Power: Set to High for all repeater channels
        - APRS: Uses the aprs_config provided to the generator

        Parameters:
        - sequence: A sequence generator providing unique internal IDs for each channel

        Side Effects:
        - Populates self._channels list with generated DigitalChannel objects
        - Each channel receives a sequential internal_id from the provided sequence
        """
        for dev in self.devices:
            if self.callsign_matcher and not self.callsign_matcher.matches(
                dev["callsign"]
            ):
                continue

            if dev["rx"] == dev["tx"] or dev["pep"] == 1 or dev["statusText"] == "DMO":
                # Hotspot
                continue

            for tg_id, slot in brandmeister.TalkgroupAPI().static_talkgroups(dev["id"]):
                if slot == 0:
                    continue
                for tg in self.talkgroups:
                    if tg.calling_id == tg_id:
                        # We were passed a TG definition

                        name = channel_label(dev["callsign"], tg)

                        # Handle None values for lat/lng
                        lat = float(dev["lat"]) if dev["lat"] is not None else None
                        lng = float(dev["lng"]) if dev["lng"] is not None else None
                        locator = (
                            mh.to_maiden(dev["lat"], dev["lng"], 3)
                            if lat is not None and lng is not None
                            else None
                        )

                        self._channels.append(
                            DigitalChannel(
                                internal_id=sequence.next(),
                                name=name,
                                rx_freq=float(dev["tx"]),
                                tx_freq=float(dev["rx"]),
                                tx_power=TxPower.High,
                                scanlist_id="-",
                                tot=None,
                                rx_only=False,
                                admit_crit="Free",
                                color=dev["colorcode"],
                                slot=slot,
                                rx_grouplist_id="-",
                                tx_contact_id=str(tg.internal_id),
                                aprs=self.aprs_config,
                                anytone=DEFAULT_ANYTONE_EXTENSIONS,
                                _lat=lat,
                                _lng=lng,
                                _locator=locator,
                                _rpt_callsign=dev["callsign"],
                                _qth=dev["city"],
                            )
                        )

            for slot in [1, 2]:
                name = " ".join(
                    [
                        dev["callsign"],
                        f"TS{slot}",
                    ]
                )

                # Handle None values for lat/lng
                lat = float(dev["lat"]) if dev["lat"] is not None else None
                lng = float(dev["lng"]) if dev["lng"] is not None else None
                locator = (
                    mh.to_maiden(dev["lat"], dev["lng"], 3)
                    if lat is not None and lng is not None
                    else None
                )

                self._channels.append(
                    DigitalChannel(
                        internal_id=sequence.next(),
                        name=name,
                        rx_freq=float(dev["tx"]),
                        tx_freq=float(dev["rx"]),
                        tx_power=TxPower.High,
                        scanlist_id="-",
                        tot=None,
                        rx_only=False,
                        admit_crit="Free",
                        color=dev["colorcode"],
                        slot=slot,
                        rx_grouplist_id="-",
                        tx_contact_id=self.default_contact_id,
                        aprs=self.aprs_config,
                        anytone=DEFAULT_ANYTONE_EXTENSIONS,
                        _lat=lat,
                        _lng=lng,
                        _locator=locator,
                        _rpt_callsign=dev["callsign"],
                        _qth=dev["city"],
                    )
                )


class DigitalPMR446ChannelGenerator:
    def __init__(self):
        self._channels = []

    def channels(self, seq):
        f = 446.003125
        for channum in range(1, 33):
            chan_freq = f + (channum - 1) * 0.00625
            name = f"dPMR {channum}"
            self._channels.append(
                DigitalChannel(
                    internal_id=seq.next(),
                    name=name,
                    rx_freq=chan_freq,
                    tx_freq=chan_freq,
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    color=int(64 * (chan_freq % 0.4)),  # per TS 102 658
                    slot=2,
                    rx_grouplist_id="-",
                    tx_contact_id=None,
                    anytone=DEFAULT_ANYTONE_EXTENSIONS,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )
        return self._channels
