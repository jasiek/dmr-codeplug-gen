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

        f = 446.00625
        for chan_num in range(1, 17):
            chan_freq = f + (chan_num - 1) * 0.0125
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
            f += 0.0125  # rounding problem here?
        return self._channels


class AnalogChannelGeneratorFromPrzemienniki:
    def __init__(self, source, power, *, aprs):
        root = source
        self._repeaters = root.findall("repeaters/repeater")
        self.power = power
        self._channels = []
        self.aprs_config = aprs

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
            self._channels.append(
                AnalogChannel(
                    internal_id=sequence.next(),
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
            )


class AnalogChannelGeneratorFromRepeaterBook:
    def __init__(self, source, power, *, aprs):
        """
        Initialize analog channel generator from RepeaterBook data

        Args:
            source: JSON data from RepeaterBook API
            power: Transmit power setting
            aprs: APRS configuration
        """
        self._repeaters = source["results"]
        self.power = power
        self._channels = []
        self.aprs_config = aprs

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for repeater in self._repeaters:
            # Skip if not analog mode or if required fields are missing
            if repeater.get("FM Analog") != "Yes":
                continue

            try:
                # Get frequencies - new format provides Input Freq directly
                rpt_output = float(repeater.get("Frequency", 0))
                rpt_input = float(repeater.get("Input Freq", 0))

                # Calculate offset to check if it's a repeater
                offset = rpt_input - rpt_output

                # Skip if no offset (not a repeater)
                if abs(offset) < 0.0001:
                    continue

                # Skip if frequencies are 0 or invalid
                if rpt_output == 0 or rpt_input == 0:
                    continue

                # Skip if not in 2m (144-148 MHz) or 70cm (420-450 MHz) bands
                if not (
                    (144.0 <= rpt_output <= 148.0) or (420.0 <= rpt_output <= 450.0)
                ):
                    continue

            except (ValueError, TypeError):
                continue

            # Get tones - check both PL and TSQ fields
            rx_tone = None
            tx_tone = None
            try:
                # Try PL first, then TSQ as fallback
                tone_str = repeater.get("PL") or repeater.get("TSQ")
                if tone_str and tone_str.strip():
                    tone_val = float(tone_str)
                    rx_tone = tone_val
                    tx_tone = tone_val
            except (ValueError, TypeError):
                pass

            # Get location data
            lat = None
            lng = None
            try:
                if repeater.get("Lat"):
                    lat = float(repeater.get("Lat"))
                if repeater.get("Long"):
                    lng = float(repeater.get("Long"))
            except (ValueError, TypeError):
                pass

            # Get callsign and location
            callsign = repeater.get("Callsign", "").strip()
            qth = repeater.get("Nearest City", "").strip()
            if not qth:
                qth = repeater.get("Landmark", "").strip()

            # Use callsign or frequency as name
            name = callsign if callsign else f"{rpt_output:.4f}"

            # Skip if we don't have a meaningful identifier
            if not name:
                continue

            self._channels.append(
                AnalogChannel(
                    internal_id=sequence.next(),
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
                    _locator=None,
                    _rpt_callsign=callsign,
                    _qth=qth,
                )
            )
