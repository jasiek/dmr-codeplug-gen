import yaml


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


class QDMRWriter:
    # NOTE: 25/12/2023 (jps): This decides how to write the sections.
    def __init__(self, file):
        self.file = file

    def start(self):
        self.codeplug = yaml.load(
            open("blank_radio/uv878_base.yml"), Loader=yaml.Loader
        )
        self.codeplug["channels"] = []

    def write_radio_config(self, dmr_id, callsign):
        pass

    def write_contacts(self, contacts):
        self.codeplug["contacts"] = []
        for contact in contacts:
            self.codeplug["contacts"].append(
                {
                    "dmr": {
                        "id": f"contact{contact.internal_id}",
                        "name": contact.name,
                        "type": contact.type.value,
                        "number": contact.calling_id,
                        "ring": False,
                    }
                }
            )

    def write_grouplists(self, grouplists):
        self.codeplug["groupLists"] = []
        for gpl in grouplists:
            self.codeplug["groupLists"].append(
                {
                    "id": f"grouplist{gpl.internal_id}",
                    "name": gpl.name,
                    "contacts": [f"contact{id}" for id in gpl.contact_ids],
                }
            )

    def write_analog_channels(self, channels):
        codeplug_channels = []
        for chan in channels:
            ch = {
                "analog": {
                    "id": f"ch{chan.internal_id}",
                    "name": chan.name,
                    "rxFrequency": chan.rx_freq,
                    "txFrequency": chan.tx_freq,
                    "power": chan.tx_power.value,
                    "timeout": chan.tot,
                    "rxOnly": chan.rx_only,
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

            codeplug_channels.append(ch)
        self.codeplug["channels"] += codeplug_channels

    def write_digital_channels(self, channels):
        codeplug_channels = []
        for chan in channels:
            ch = {
                "digital": {
                    "id": f"ch{chan.internal_id}",
                    "name": chan.name,
                    "rxFrequency": chan.rx_freq,
                    "txFrequency": chan.tx_freq,
                    "power": chan.tx_power.value,
                    "timeout": chan.tot,
                    "rxOnly": chan.rx_only,
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

            codeplug_channels.append(ch)
        self.codeplug["channels"] += codeplug_channels

    def write_zones(self, zones):
        self.codeplug["zones"] = []
        for z in zones:
            self.codeplug["zones"].append(
                {
                    "id": f"zone{z.internal_id}",
                    "name": z.name,
                    "A": [f"ch{id}" for id in z.channels],
                }
            )

    def write_roaming_channels(self, channels):
        self.codeplug["roamingChannels"] = []
        for ch in channels:
            channel = {
                "id": f"roamingchan{ch.internal_id}",
                "name": ch.name,
                "rxFrequency": ch.rx_freq,
                "txFrequency": ch.tx_freq,
                "colorCode": ch.color,
                "timeSlot": f"TS{ch.slot}",
            }
            self.codeplug["roamingChannels"].append(channel)

    def write_roaming_zones(self, zones):
        self.codeplug["roamingZones"] = []
        for z in zones:
            zone = {
                "id": f"roamingzone{z.internal_id}",
                "name": z.name,
                "channels": [f"roamingchan{c}" for c in z.channels],
            }
            self.codeplug["roamingZones"].append(zone)

    def finish(self):
        self.file.write(
            yaml.dump(
                self.codeplug,
                explicit_start=True,
                explicit_end=True,
                sort_keys=False,
                Dumper=IndentDumper,
                version=(1, 2),
            )
        )
        self.file.close()