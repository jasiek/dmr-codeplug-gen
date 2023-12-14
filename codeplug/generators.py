import json
from lxml import etree
from models import Contact, GroupList, AnalogChannel


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


class AnalogChannelGeneratorFromPrzemienniki:
    def __init__(self, filename, power):
        root = etree.parse(filename)
        self._repeaters = root.findall("//repeater")
        self.power = power

    def channels(self):
        i = 1
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

            yield AnalogChannel(
                internal_id=i,
                name=node.find("qra").text,
                rx_freq=rpt_output,
                tx_freq_or_offset=tx_offset,
                tx_power="High",
                scanlist_id="-",
                tot="-",
                rx_only="-",
                admit_crit="Free",
                squelch="Normal",
                rx_tone=rx_tone,
                tx_tone=tx_tone,
                width=12.5,
            )
            i += 1
