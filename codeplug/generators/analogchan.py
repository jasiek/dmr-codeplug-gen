from lxml import etree
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
                    tx_power=TxPower.Min,
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
            if node.find("status").text != "WORKING":
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
