from generators import Sequence  # NOTE: 02/01/2024 (jps): Not sure this belongs here.


class AT878UV:
    # NOTE: 25/12/2023 (jps): This decides which sections to write.
    def __init__(
        self,
        *,
        dmr_id,  # unused atm
        callsign,  # unused atm
        analog_aprs_config,
        digital_aprs_config,
        contacts=[],
        grouplists=[],
        analog_channels=[],
        digital_channels=[],
        zones=[],
        roaming_channels=[],
        roaming_zones=[],
    ):
        self.dmr_id = dmr_id
        self.callsign = callsign
        self.contacts = contacts
        self.grouplists = grouplists
        self.analog_channels = analog_channels
        self.digital_channels = digital_channels
        self.zones = zones
        self.roaming_channels = roaming_channels
        self.roaming_zones = roaming_zones

        self.analog_aprs_config = analog_aprs_config
        self.digital_aprs_config = digital_aprs_config

    def generate(self, writer):
        writer.start()
        writer.write_radio_config(self.dmr_id, self.callsign)
        writer.write_contacts(self.contacts)
        writer.write_grouplists(self.grouplists)
        writer.write_analog_channels(self.analog_channels)
        writer.write_digital_channels(self.digital_channels)
        writer.write_zones(self.zones)
        writer.write_roaming_channels(self.roaming_channels)
        writer.write_roaming_zones(self.roaming_zones)
        writer.write_analog_aprs(self.analog_aprs_config)
        writer.write_digital_aprs(self.digital_aprs_config)
        writer.write_sms_configuration()
        writer.finish()
