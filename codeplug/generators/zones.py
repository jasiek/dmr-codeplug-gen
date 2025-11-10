import re
from collections import defaultdict

from generators import Sequence
from models import Zone, DigitalChannel, is_hotspot, AnalogChannel

# Import the new location-based zone generators
from .location_zones import LocationClusterZoneGenerator, DistanceBandedZoneGenerator


class ZoneFromLocatorGenerator:
    def __init__(self, channels, filter_chain=None, debug=False):
        self.channels = channels
        self.filter_chain = filter_chain
        self.debug = debug

    def zones(self, seq):
        locators_to_channels = defaultdict(lambda: [])

        # Pre-filter channels if filter chain is provided
        filtered_channels = self.channels
        if self.filter_chain:
            filtered_channels = []
            for chan in self.channels:
                should_include, reason = self.filter_chain.should_include(chan)
                if should_include:
                    filtered_channels.append(chan)
                elif self.debug:
                    print(
                        f"[ZoneFromLocatorGenerator] Filtered out channel: {chan.name} - {reason}"
                    )

        for chan in filtered_channels:
            if chan.locator is None:
                continue

            locator = chan.locator[0:4]
            if isinstance(chan, DigitalChannel):
                locator_label = f"Digital {locator}"
            else:
                locator_label = f"Analog {locator}"

            if chan.locator == "":
                locators_to_channels["No locator"] += [chan]
            else:
                locators_to_channels[locator_label] += [chan]

        output = []

        for key in sorted(locators_to_channels.keys()):
            channels = sorted(locators_to_channels[key], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]
            output.append(Zone(internal_id=seq.next(), name=key, channels=channel_ids))

        return output[:250]


class ZoneFromCallsignGenerator:
    def __init__(self, channels, filter_chain=None, debug=False):
        self.channels = channels
        self.filter_chain = filter_chain
        self.debug = debug

    def zones(self, seq):
        prefix_to_channels = defaultdict(lambda: [])

        # Pre-filter channels if filter chain is provided
        filtered_channels = self.channels
        if self.filter_chain:
            filtered_channels = []
            for chan in self.channels:
                should_include, reason = self.filter_chain.should_include(chan)
                if should_include:
                    filtered_channels.append(chan)
                elif self.debug:
                    print(
                        f"[ZoneFromCallsignGenerator] Filtered out channel: {chan.name} - {reason}"
                    )

        for chan in filtered_channels:
            if m := re.match("^([A-Z]{2}[0-9])", chan._rpt_callsign):
                prefix = m.groups()[0]
                if isinstance(chan, DigitalChannel):
                    label = f"{prefix} Digital"
                else:
                    label = f"{prefix} Analog"
                prefix_to_channels[label] += [chan]

        output = []
        for key in sorted(prefix_to_channels.keys()):
            channels = sorted(prefix_to_channels[key], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]
            output.append(Zone(internal_id=seq.next(), name=key, channels=channel_ids))
        return output[:250]


class ZoneFromCallsignGenerator2:
    # NOTE: 26/12/2023 (jps): Per-callsign clustering of channels
    def __init__(self, channels, with_qth=True, filter_chain=None, debug=False):
        self.channels = channels
        self.with_qth = with_qth
        self.filter_chain = filter_chain
        self.debug = debug

    def zones(self, seq):
        callsign_to_channels = defaultdict(lambda: [])

        # Pre-filter channels if filter chain is provided
        filtered_channels = self.channels
        if self.filter_chain:
            filtered_channels = []
            for chan in self.channels:
                should_include, reason = self.filter_chain.should_include(chan)
                if should_include:
                    filtered_channels.append(chan)
                elif self.debug:
                    print(
                        f"[ZoneFromCallsignGenerator2] Filtered out channel: {chan.name} - {reason}"
                    )

        for chan in filtered_channels:
            callsign_to_channels[chan._rpt_callsign].append(chan)

        output = []

        for key in sorted(callsign_to_channels.keys()):
            channels = sorted(callsign_to_channels[key], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]
            if self.with_qth:
                name = f"{key} {channels[0]._qth}"
            else:
                name = key
            output.append(Zone(internal_id=seq.next(), name=name, channels=channel_ids))
        return output[:250]


class PMRZoneGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        return [
            Zone(
                internal_id=seq.next(),
                name="PMR",
                channels=[ch.internal_id for ch in self.channels],
            )
        ]


class AnalogZoneGenerator:
    def __init__(self, channels, zone_name="Analog"):
        self.channels = channels
        self.zone_name = zone_name

    def zones(self, seq):
        analog_channels = []
        for chan in self.channels:
            if isinstance(chan, AnalogChannel):
                analog_channels.append(chan.internal_id)

        if len(analog_channels) == 0:
            print(f"No analog channels found, skipping zone '{self.zone_name}'.")
            return []

        if len(analog_channels) > 250:
            print(
                f"Too many analog channels for zone ({len(analog_channels)}) '{self.zone_name}', truncating to 250."
            )
            analog_channels = analog_channels[:250]

        return [
            Zone(internal_id=seq.next(), name=self.zone_name, channels=analog_channels),
        ][:250]


class AnalogZoneByBandGenerator:
    def __init__(self, channels, prefix, filter_chain=None, debug=False):
        self.channels = channels
        self.prefix = prefix
        self.filter_chain = filter_chain
        self.debug = debug

    def zones(self, seq):
        zones = {}

        # Pre-filter channels if filter chain is provided
        filtered_channels = self.channels
        if self.filter_chain:
            filtered_channels = []
            for chan in self.channels:
                should_include, reason = self.filter_chain.should_include(chan)
                if should_include:
                    filtered_channels.append(chan)
                elif self.debug:
                    print(
                        f"[AnalogZoneByBandGenerator] Filtered out channel: {chan.name} - {reason}"
                    )

        for chan in filtered_channels:
            if isinstance(chan, AnalogChannel):
                if chan.band() not in zones:
                    zones[chan.band()] = []
                zones[chan.band()].append(chan.internal_id)

        return [
            Zone(
                internal_id=seq.next(),
                name=f"{self.prefix} {band} Analog",
                channels=channel_ids,
            )
            for band, channel_ids in zones.items()
        ][:250]


class HotspotZoneGenerator:
    def __init__(self, channels):
        self.channels = channels

    def zones(self, seq):
        hotspot_channels = []
        for chan in self.channels:
            if is_hotspot(chan):
                hotspot_channels.append(chan.internal_id)

        return [
            Zone(internal_id=seq.next(), name="Hotspot", channels=hotspot_channels)
        ][:250]
