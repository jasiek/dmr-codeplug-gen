from lxml import etree
import json
import maidenhead as mh

from models import AnalogChannel, TxPower, ChannelWidth


class AnalogPMR446ChannelGenerator:
    def __init__(self, *, aprs):
        self._channels = []
        self.aprs_config = aprs

    def channels(self, sequence):
        if self._channels != []:
            return self._channels

        base_freq = 446.00625
        for chan_num in range(1, 17):
            chan_freq = base_freq + (chan_num - 1) * 0.0125
            self._channels.append(
                AnalogChannel(
                    internal_id=sequence.next(),
                    name=f"PMR {chan_num}",
                    rx_freq=chan_freq,
                    tx_freq=chan_freq,
                    tx_power=TxPower.Low,
                    scanlist_id="-",
                    tot=None,
                    rx_only=False,
                    admit_crit="Free",
                    squelch=1,
                    rx_tone=110.9,
                    tx_tone=110.9,
                    width=ChannelWidth.Narrow,
                    aprs=self.aprs_config,
                    _lat=None,
                    _lng=None,
                    _locator=None,
                    _rpt_callsign=None,
                    _qth=None,
                )
            )
        return self._channels


class AnalogChannelGeneratorFromPrzemienniki:
    def __init__(self, source, power, *, aprs, filter_chain=None, debug=False):
        root = source
        self._repeaters = root.findall("repeaters/repeater")
        self.power = power
        self._channels = []
        self.aprs_config = aprs
        self.filter_chain = filter_chain
        self.debug = debug

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for node in self._repeaters:
            if node.find("status").text not in ["WORKING", "TESTING"]:
                continue

            if len(node.findall("band")) > 1:
                continue

            if len(node.findall("qrg")) > 2:
                continue

            rpt_output = float(node.xpath('./qrg[@type="tx"]')[0].text)
            rpt_input = float(node.xpath('./qrg[@type="rx"]')[0].text)
            tx_offset = rpt_input - rpt_output

            if abs(tx_offset) < 0.0001:
                continue

            rx_tone = None
            tx_tone = None
            if node.find("ctcss") is not None:
                rx_tone_node = node.xpath('./ctcss[@type="tx"]')
                if len(rx_tone_node) > 0:
                    rx_tone = float(rx_tone_node[0].text)

                tx_tone_node = node.xpath('./ctcss[@type="rx"]')
                if len(tx_tone_node) > 0:
                    tx_tone = float(tx_tone_node[0].text)

            lat = None
            lng = None
            locator = None
            if node.find("location") is not None:
                try:
                    lat = float(node.find("latitude").text)
                    lng = float(node.find("longitude").text)
                    locator = node.find("locator").text
                except AttributeError:
                    pass

            callsign = node.find("qra").text
            qth = node.find("qth").text

            # Create channel without ID first for filtering
            channel = AnalogChannel(
                internal_id=None,  # Will be assigned after filtering
                name=callsign,
                rx_freq=rpt_output,
                tx_freq=rpt_input,
                tx_power=TxPower.High,
                scanlist_id="-",
                tot=None,
                rx_only=False,
                admit_crit="Free",
                squelch=1,
                rx_tone=rx_tone,
                tx_tone=tx_tone,
                width=ChannelWidth.Narrow,
                aprs=self.aprs_config,
                _lat=lat,
                _lng=lng,
                _locator=locator,
                _rpt_callsign=callsign,
                _qth=qth,
            )

            # Apply filter chain if provided
            if self.filter_chain:
                should_include, reason = self.filter_chain.should_include(channel)
                if not should_include:
                    if self.debug:
                        print(
                            f"[AnalogChannelGeneratorFromPrzemienniki] Filtered out: {callsign} - {reason}"
                        )
                    continue

            # Assign ID and add to channels list
            channel.internal_id = sequence.next()
            self._channels.append(channel)


class AnalogChannelGeneratorFromRepeaterBook:
    def __init__(self, source, power, *, aprs, filter_chain=None, debug=False):
        """
        Initialize analog channel generator from RepeaterBook data

        Args:
            source: RXF XML root from api.codeplug.org (radio perspective)
            power: Transmit power setting
            aprs: APRS configuration
            filter_chain: Optional FilterChain for pre-filtering channels
            debug: If True, print debug information for filtered channels
        """
        self._repeaters = source.findall("repeaters/repeater")
        self.power = power
        self._channels = []
        self.aprs_config = aprs
        self.filter_chain = filter_chain
        self.debug = debug

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    @staticmethod
    def _float(node, path):
        found = node.xpath(path)
        if not found or not (found[0].text or "").strip():
            return None
        try:
            return float(found[0].text)
        except ValueError:
            return None

    def generate_channels(self, sequence):
        for node in self._repeaters:
            if node.findtext("mode") != "fm":
                continue

            # Radio perspective: rx is the repeater output, tx its input
            rpt_output = self._float(node, './qrg[@type="rx"]')
            rpt_input = self._float(node, './qrg[@type="tx"]')

            # Skip if frequencies are missing or invalid
            if not rpt_output or not rpt_input:
                continue

            # Skip if no offset (not a repeater)
            if abs(rpt_input - rpt_output) < 0.0001:
                continue

            rx_tone = self._float(node, './ctcss[@type="rx"]')
            tx_tone = self._float(node, './ctcss[@type="tx"]')

            lat = self._float(node, "./location/latitude")
            lng = self._float(node, "./location/longitude")

            # qth is "City, State, County"; keep the city for the channel name
            callsign = (node.findtext("qra") or "").strip()
            qth = (node.findtext("qth") or "").split(",")[0].strip()

            # Use callsign or frequency as name
            name = f"{callsign} {qth}".strip()

            # Skip if we don't have a meaningful identifier
            if not name:
                continue

            # Create channel without ID first for filtering
            channel = AnalogChannel(
                internal_id=None,  # Will be assigned after filtering
                name=name,
                rx_freq=rpt_output,
                tx_freq=rpt_input,
                tx_power=TxPower.High,
                scanlist_id="-",
                tot=None,
                rx_only=False,
                admit_crit="Free",
                squelch=1,
                rx_tone=rx_tone,
                tx_tone=tx_tone,
                width=ChannelWidth.Narrow,
                aprs=self.aprs_config,
                _lat=lat,
                _lng=lng,
                _locator=(node.findtext("location/locator") or None),
                _rpt_callsign=callsign,
                _qth=qth,
            )

            # Apply filter chain if provided
            if self.filter_chain:
                should_include, reason = self.filter_chain.should_include(channel)
                if not should_include:
                    if self.debug:
                        print(
                            f"[AnalogChannelGeneratorFromRepeaterBook] Filtered out: {name} - {reason}"
                        )
                    continue

            # Assign ID and add to channels list
            channel.internal_id = sequence.next()
            self._channels.append(channel)
