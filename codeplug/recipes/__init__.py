class BaseRecipe:
    def __init__(self, callsign, dmr_id, filename, radio_class, writer_class):
        self.callsign = callsign
        self.dmr_id = dmr_id
        self.filename = filename
        self.radio_class = radio_class
        self.writer_class = writer_class

        self.roaming_channels = []
        self.contacts = []
        self.grouplists = []
        self.analog_channels = []
        self.digital_channels = []
        self.zones = []
        self.roaming_zones = []

    def generate(self):
        self.prepare()
        with open(self.filename, "wt") as f:
            writer = self.writer_class(f)
            self.radio_class(
                dmr_id=self.dmr_id,
                callsign=self.callsign,
                contacts=self.contacts,
                grouplists=self.grouplists,
                analog_channels=self.analog_channels,
                digital_channels=self.digital_channels,
                zones=self.zones,
                roaming_channels=self.roaming_channels,
                roaming_zones=self.roaming_zones,
                analog_aprs_config=self.analog_aprs_config,
                digital_aprs_config=self.digital_aprs_config,
            ).generate(writer)
