import json
import yaml

from unidecode import unidecode

from generators import Sequence
from generators.zones import ZoneFromLocatorGenerator

CONTACT_NAME_MAX = 16  # https://github.com/OpenRTX/dmrconfig/blob/master/d868uv.c#L317

# TODO:
#
# Scanlists
# Messages (low prio)
# Intro lines (low prio)


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


class Codeplug:
    def __init__(
        self,
        contact_gen,
        grouplist_gen,
        dmr_id,
        callsign,
        analog_chan_gen,
        digital_chan_gen,
    ):
        self.contact_gen = contact_gen
        self.grouplist_gen = grouplist_gen
        self.dmr_id = dmr_id
        self.callsign = callsign
        self.analog_chan_gen = analog_chan_gen
        self.digital_chan_gen = digital_chan_gen
        self.sequence = Sequence()
        self.zone_gen = ZoneFromLocatorGenerator(analog_chan_gen, digital_chan_gen)

    def generate(self, file):
        codeplug = yaml.load(open("blank_radio/uv878_base.yml"), Loader=yaml.Loader)
        codeplug["channels"] = []

        self.generate_contacts(codeplug)
        self.generate_grouplists(codeplug)
        self.generate_analog_channels(codeplug)
        self.generate_digital_channels(codeplug)
        self.generate_zones(codeplug)

        file.write(
            yaml.dump(
                codeplug,
                explicit_start=True,
                explicit_end=True,
                sort_keys=False,
                Dumper=IndentDumper,
                version=(1, 2),
            )
        )
        file.close()

    def generate_contacts(self, codeplug):
        contacts = []
        for contact in self.contact_gen.contacts():
            contacts.append(
                {
                    "dmr": {
                        "id": f"contact{contact.internal_id}",
                        "name": self._format_contact_name(contact.name),
                        "type": "GroupCall",
                        "number": contact.calling_id,
                        "ring": False,
                    }
                }
            )
        codeplug["contacts"] = contacts

    def generate_grouplists(self, codeplug):
        grouplists = []
        for gpl in self.grouplist_gen.grouplists():
            grouplists.append(
                {
                    "id": f"grouplist{gpl.internal_id}",
                    "name": self._format_contact_name(gpl.name),
                    "contacts": [f"contact{id}" for id in gpl.contact_ids],
                }
            )

        codeplug["groupLists"] = grouplists

    def generate_analog_channels(self, codeplug):
        channels = []
        for chan in self.analog_chan_gen.channels(self.sequence):
            ch = {
                "analog": {
                    "id": f"ch{chan.internal_id}",
                    "name": chan.name,
                    "rxFrequency": chan.rx_freq,
                    "txFrequency": chan.tx_freq,
                    "power": chan.tx_power,
                    "timeout": 0,
                    # "rxOnly": False,
                    # "vox": False,
                    "scanList": chan.scanlist_id,
                    "admit": chan.admit_crit,
                    "squelch": 1,
                    "bandwidth": "Narrow",
                }
            }

            if chan.rx_tone:
                ch["analog"]["rxTone"] = chan.rx_tone

            if chan.tx_tone:
                ch["analog"]["txTone"] = chan.tx_tone

            channels.append(ch)
        codeplug["channels"] += channels

    def generate_digital_channels(self, codeplug):
        channels = []
        for chan in self.digital_chan_gen.channels(self.sequence):
            ch = {
                "digital": {
                    "id": f"ch{chan.internal_id}",
                    "name": chan.name,
                    "rxFrequency": chan.rx_freq,
                    "txFrequency": chan.tx_freq,
                    "power": chan.tx_power,
                    "timeout": 0,
                    # "rxOnly": False,
                    # "vox": False,
                    "scanList": chan.scanlist_id,
                    "admit": chan.admit_crit,
                    "colorCode": chan.color,
                    "timeSlot": f"TS{chan.slot}",
                }
            }
            if chan.tx_contact_id != "-":
                ch["digital"]["contact"] = f"contact{chan.tx_contact_id}"

            channels.append(ch)
        codeplug["channels"] += channels

    def generate_zones(self, codeplug):
        zones = []
        for z in self.zone_gen.zones():
            zones.append(
                {
                    "id": f"zone{z.internal_id}",
                    "name": z.name,
                    "A": [f"ch{id}" for id in z.channels],
                }
            )
        codeplug["zones"] = zones

    def _format_contact_name(self, name):
        # NOTE: 13/06/2023 (jps): Only ascii characters are permitted
        name = unidecode(name)
        # NOTE: 13/06/2023 (jps): Max size of contact name
        name = name[:CONTACT_NAME_MAX]
        return name.replace(" ", "_").ljust(CONTACT_NAME_MAX)
