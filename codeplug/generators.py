import json
import maidenhead as mh
from collections import defaultdict
from lxml import etree
from models import Contact, GroupList, AnalogChannel, DigitalChannel, Zone


class BrandmeisterTGContactGenerator:
    def __init__(self):
        self._contacts = json.load(open("data/brandmeister_talkgroups.json"))

    def contacts(self):
        i = 1
        for key in self._contacts:
            yield Contact(
                internal_id=i,
                name=self._sanitize_contact(self._contacts[key]),
                calling_id=int(key),
            )
            i += 1

    def _sanitize_contact(self, name):
        # NOTE: 13/06/2023 (jps): Some contact names contain newlines (!)
        return name.strip("\r\n")


class CountryGroupListGenerator:
    # Group groups by country, if possible
    def __init__(self, contacts, country_id):
        self._contacts = contacts
        self._country_id = str(country_id)

    def grouplists(self):
        matching_ids = [
            contact.internal_id
            for contact in self._contacts
            if str(contact.calling_id).startswith(self._country_id)
        ]
        i = 1
        yield GroupList(internal_id=i, name="Poland", contact_ids=matching_ids)


class ZoneFromLocatorGenerator:
    def __init__(self, *chan_gens):
        self.chan_gens = chan_gens
        self.locators_to_channels = defaultdict(lambda: [])

    def zones(self):
        s = Sequence()
        for chan_gen in self.chan_gens:
            for chan in chan_gen.channels(s):
                if chan.locator is None or chan.locator == "":
                    continue
                locator = chan.locator[0:4]
                self.locators_to_channels[locator] += [chan.internal_id]

        zs = Sequence()
        for key in self.locators_to_channels.keys():
            value = sorted(self.locators_to_channels[key])
            yield Zone(internal_id=zs.next(), name=key, channels=value)


class Sequence:
    def __init__(self, start=0):
        self.i = start

    def next(self):
        self.i += 1
        return self.i


class ChannelAggregator:
    def __init__(self, gen1, gen2):
        self.gen1 = gen1
        self.gen2 = gen2

    def channels(self, sequence):
        for chan in self.gen1.channels(sequence):
            yield chan
        for chan in self.gen2.channels(sequence):
            yield chan


class DigitalChannelGeneratorFromBrandmeister:
    def __init__(self, filename, power):
        self.devices = json.load(open(filename))

    def channels(self, sequence):
        for dev in self.devices:
            if dev["rx"] == dev["tx"] or dev["pep"] == 1 or dev["statusText"] == "DMO":
                # Hotspot
                continue

            yield DigitalChannel(
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


class AnalogChannelGeneratorFromPrzemienniki:
    def __init__(self, filename, power):
        root = etree.parse(filename)
        self._repeaters = root.findall("//repeater")
        self.power = power

    def channels(self, sequence):
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

            yield AnalogChannel(
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
