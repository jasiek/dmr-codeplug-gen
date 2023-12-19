import json

from lxml import etree
import maidenhead as mh

from models import DigitalChannel, AnalogChannel


class HotspotDigitalChannelGenerator:
    def __init__(self, talkgroups, ts=2, f=438.800, color=1):
        self.f = f
        self.ts = ts
        self.color = color
        self.talkgroups = talkgroups
        self._channels = []

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for tg in self.talkgroups:
            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=self._format(f"HS {tg.calling_id} {tg.name}"),
                    rx_freq=self.f,
                    tx_freq=self.f,
                    tx_power="Low",
                    scanlist_id="-",
                    tot="-",
                    rx_only="-",
                    admit_crit="Free",
                    color=self.color,
                    slot=self.ts,
                    rx_grouplist_id="-",
                    tx_contact_id=str(tg.internal_id),
                    lat=0.0,
                    lng=0.0,
                    locator="",
                )
            )

    def _format(self, string):
        return string[0:16]


class DigitalChannelGeneratorFromBrandmeister:
    def __init__(self, filename, power):
        self.devices = json.load(open(filename))
        self._channels = []

    def channels(self, sequence):
        if len(self._channels) == 0:
            self.generate_channels(sequence)
        return self._channels

    def generate_channels(self, sequence):
        for dev in self.devices:
            if dev["rx"] == dev["tx"] or dev["pep"] == 1 or dev["statusText"] == "DMO":
                # Hotspot
                continue

            self._channels.append(
                DigitalChannel(
                    internal_id=sequence.next(),
                    name=dev["callsign"],
                    rx_freq=float(dev["rx"]),
                    tx_freq=float(dev["tx"]),
                    tx_power="High",
                    scanlist_id="-",
                    tot="-",
                    rx_only="-",
                    admit_crit="Free",
                    color=dev["colorcode"],
                    slot=2,
                    rx_grouplist_id="-",
                    tx_contact_id="-",
                    lat=float(dev["lat"]),
                    lng=float(dev["lng"]),
                    locator=mh.to_maiden(dev["lat"], dev["lng"], 3),
                )
            )


class AnalogChannelGeneratorFromPrzemienniki:
    def __init__(self, filename, power):
        root = etree.parse(filename)
        self._repeaters = root.findall("//repeater")
        self.power = power
        self._channels = []

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

            rpt_output = float(node.xpath('./qrg[@type="rx"]')[0].text)
            rpt_input = float(node.xpath('./qrg[@type="tx"]')[0].text)
            tx_offset = rpt_input - rpt_output

            if tx_offset < 0.0001:
                continue

            rx_tone = "-"
            tx_tone = "-"
            if node.find("ctcss") is not None:
                rx_tone_node = node.xpath('./ctcss[@type="tx"]')
                if len(rx_tone_node) > 0:
                    rx_tone = str(float(rx_tone_node[0].text))

                tx_tone_node = node.xpath('./ctcss[@type="rx"]')
                if len(tx_tone_node) > 0:
                    tx_tone = str(float(tx_tone_node[0].text))

            lat = 0.0
            lng = 0.0
            locator = ""
            if node.find("location") is not None:
                try:
                    lat = float(node.find("latitude").text)
                    lng = float(node.find("longitude").text)
                    locator = node.find("locator").text
                except AttributeError:
                    pass

            self._channels.append(
                AnalogChannel(
                    internal_id=sequence.next(),
                    name=node.find("qra").text,
                    rx_freq=rpt_output,
                    tx_freq=rpt_input,
                    tx_power="High",
                    scanlist_id="-",
                    tot="-",
                    rx_only="-",
                    admit_crit="Free",
                    squelch="Normal",
                    rx_tone=rx_tone,
                    tx_tone=tx_tone,
                    width=12.5,
                    lat=lat,
                    lng=lng,
                    locator=locator,
                )
            )