class BaseRecipe:
    def __init__(
        self, callsign, dmr_id, filename, radio_class, writer_class, timezone=None
    ):
        self.callsign = callsign
        self.dmr_id = dmr_id
        self.filename = filename
        self.radio_class = radio_class
        self.writer_class = writer_class
        self.timezone = timezone
        # Subclasses can define their own location as (latitude, longitude)
        self.location = None

        self.roaming_channels = []
        self.contacts = []
        self.grouplists = []
        self.analog_channels = []
        self.digital_channels = []
        self.zones = []
        self.roaming_zones = []
        self.scanlists = []

    def prepare(self):
        """Main preparation method that orchestrates all section preparation."""
        from generators import Sequence

        # Create sequences for each section
        self.contact_seq = Sequence()
        self.aprs_seq = Sequence()
        self.chan_seq = Sequence()
        self.zone_seq = Sequence()
        self.rch_seq = Sequence()

        # Prepare each section in order (contacts first as they're used by channels)
        self.prepare_contacts()
        self.prepare_aprs()
        self.prepare_digital_channels()
        self.prepare_analog_channels()
        self.prepare_zones()
        self.prepare_roaming()
        self.prepare_scanlists()
        self.prepare_grouplists()

    def prepare_contacts(self):
        """Prepare DMR contacts. Override in subclasses."""
        pass

    def prepare_aprs(self):
        """Prepare APRS configurations. Override in subclasses."""
        pass

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels. Override in subclasses."""
        pass

    def prepare_analog_channels(self):
        """Prepare analog (FM) channels. Override in subclasses."""
        pass

    def prepare_zones(self):
        """Prepare channel zones. Override in subclasses."""
        pass

    def prepare_roaming(self):
        """Prepare roaming channels and zones. Override in subclasses."""
        pass

    def prepare_scanlists(self):
        """Prepare scan lists. Override in subclasses."""
        pass

    def prepare_grouplists(self):
        """Prepare talkgroup lists. Override in subclasses."""
        pass

    def generate(self):
        self.prepare()
        with open(self.filename, "wt") as f:
            writer = self.writer_class(f)
            self.radio_class(
                dmr_id=self.dmr_id,
                callsign=self.callsign,
                contacts=self.contacts,
                grouplists=self.grouplists,
                scanlists=self.scanlists,
                analog_channels=self.analog_channels,
                digital_channels=self.digital_channels,
                zones=self.zones,
                roaming_channels=self.roaming_channels,
                roaming_zones=self.roaming_zones,
                analog_aprs_config=self.analog_aprs_config,
                digital_aprs_config=self.digital_aprs_config,
                timezone=self.timezone,
            ).generate(writer)
