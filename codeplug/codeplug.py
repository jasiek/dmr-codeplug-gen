import json
import yaml

from unidecode import unidecode


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


class Codeplug:
    def __init__(
        self,
        contacts,
        grouplists,
        dmr_id,
        callsign,
        analog_channels,
        digital_channels,
        zones,
        roaming_channels,
        roaming_zones,
    ):
        self.contacts = contacts
        self.grouplists = grouplists
        self.dmr_id = dmr_id
        self.callsign = callsign
        self.analog_channels = analog_channels
        self.digital_channels = digital_channels
        self.zones = zones
        self.roaming_channels = roaming_channels
        self.roaming_zones = roaming_zones

    def generate(self, file):
        codeplug = yaml.load(open("blank_radio/uv878_base.yml"), Loader=yaml.Loader)
        codeplug["channels"] = []

        self.generate_contacts(codeplug)
        self.generate_grouplists(codeplug)
        self.generate_analog_channels(codeplug)
        self.generate_digital_channels(codeplug)
        self.generate_zones(codeplug)
        self.generate_roaming_channels(codeplug)
        self.generate_roaming_zones(codeplug)

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
        for contact in self.contacts:
            contacts.append(
                {
                    "dmr": {
                        "id": f"contact{contact.internal_id}",
                        "name": self._format_contact_name(contact.name),
                        "type": contact.type.value,
                        "number": contact.calling_id,
                        "ring": False,
                    }
                }
            )
        codeplug["contacts"] = contacts

    def generate_grouplists(self, codeplug):
        grouplists = []
        for gpl in self.grouplists:
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
        for chan in self.analog_channels:
            ch = {
                "analog": {
                    "id": f"ch{chan.internal_id}",
                    "name": chan.name,
                    "rxFrequency": chan.rx_freq,
                    "txFrequency": chan.tx_freq,
                    "power": chan.tx_power.value,
                    "timeout": 0,
                    # "rxOnly": False,
                    # "vox": False,
                    "scanList": chan.scanlist_id,
                    "admit": chan.admit_crit,
                    "squelch": 1,
                    "bandwidth": chan.width.value,
                }
            }

            if chan.rx_tone:
                ch["analog"]["rxTone"] = {"ctcss": chan.rx_tone}

            if chan.tx_tone:
                ch["analog"]["txTone"] = {"ctcss": chan.tx_tone}

            channels.append(ch)
        codeplug["channels"] += channels

    def generate_digital_channels(self, codeplug):
        channels = []
        for chan in self.digital_channels:
            ch = {
                "digital": {
                    "id": f"ch{chan.internal_id}",
                    "name": chan.name,
                    "rxFrequency": chan.rx_freq,
                    "txFrequency": chan.tx_freq,
                    "power": chan.tx_power.value,
                    "timeout": 0,
                    # "rxOnly": False,
                    # "vox": False,
                    "scanList": chan.scanlist_id,
                    "admit": chan.admit_crit,
                    "colorCode": chan.color,
                    "timeSlot": f"TS{chan.slot}",
                    "anytone": {
                        "sms": True,
                        "smsConfirm": True,
                    },
                }
            }
            if chan.tx_contact_id:
                ch["digital"]["contact"] = f"contact{chan.tx_contact_id}"

            channels.append(ch)
        codeplug["channels"] += channels

    def generate_zones(self, codeplug):
        zones = []
        for z in self.zones:
            zones.append(
                {
                    "id": f"zone{z.internal_id}",
                    "name": z.name,
                    "A": [f"ch{id}" for id in z.channels],
                }
            )
        codeplug["zones"] = zones

    def generate_roaming_channels(self, codeplug):
        roaming_channels = []
        for ch in self.roaming_channels:
            channel = {
                "id": f"roamingchan{ch.internal_id}",
                "name": ch.name,
                "rxFrequency": ch.rx_freq,
                "txFrequency": ch.tx_freq,
                "colorCode": ch.color,
                "timeSlot": f"TS{ch.slot}",
            }
            roaming_channels.append(channel)
        codeplug["roamingChannels"] = roaming_channels

    def generate_roaming_zones(self, codeplug):
        roaming_zones = []
        for z in self.roaming_zones:
            zone = {
                "id": f"roamingzone{z.internal_id}",
                "name": z.name,
                "channels": [f"roamingchan{c}" for c in z.channels],
            }
            roaming_zones.append(zone)
        codeplug["roamingZones"] = roaming_zones

    def _format_contact_name(self, name):
        # NOTE: 13/06/2023 (jps): Only ascii characters are permitted
        return unidecode(name)
