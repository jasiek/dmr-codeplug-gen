class BaseRecipe:
    def __init__(
        self,
        callsign,
        dmr_id,
        filename,
        radio_class,
        writer_class,
        timezone=None,
        debug=False,
        aprs_region="EU",
    ):
        self.callsign = callsign
        self.dmr_id = dmr_id
        self.filename = filename
        self.radio_class = radio_class
        self.writer_class = writer_class
        self.timezone = timezone
        self.debug = debug
        self.aprs_region = aprs_region  # "EU" or "US"
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

        # APRS-related attributes initialized in prepare_aprs_contacts()
        self.aprs_contact = None
        self.analog_aprs = None
        self.digital_aprs_config = None
        self.analog_aprs_config = None

    def prepare(self):
        """Main preparation method that orchestrates all section preparation."""
        from generators import Sequence

        # Create sequences for each section
        self.contact_seq = Sequence()
        self.aprs_seq = Sequence()
        self.chan_seq = Sequence()
        self.zone_seq = Sequence()
        self.rch_seq = Sequence()

        # Prepare APRS contacts first (needed by both contacts and APRS config)
        self.prepare_aprs_contacts()

        # Prepare each section in order (contacts first as they're used by channels)
        self.prepare_contacts()
        self.prepare_aprs()
        self.prepare_digital_channels()
        self.prepare_analog_channels()
        self.prepare_zones()
        self.prepare_roaming()
        self.prepare_scanlists()
        self.prepare_grouplists()

    def prepare_aprs_contacts(self):
        """Prepare APRS digital contact. Called before prepare_contacts()."""
        from generators.contacts import APRSDigitalContactGenerator

        aprs_contact_gen = APRSDigitalContactGenerator()
        self.aprs_contact = aprs_contact_gen.contacts(self.contact_seq)[0]
        return aprs_contact_gen

    def prepare_contacts(self):
        """Prepare DMR contacts. Override in subclasses."""
        pass

    def prepare_aprs(self):
        """Prepare APRS configurations for both digital and analog modes."""
        from generators.aprs import AnalogAPRSGenerator, DigitalAPRSGenerator

        # Digital APRS configuration
        digital_aprs_gen = DigitalAPRSGenerator(aprs_contact=self.aprs_contact)
        self.digital_aprs_config = digital_aprs_gen.digital_aprs_config(self.aprs_seq)

        # Analog APRS configuration
        self.analog_aprs = AnalogAPRSGenerator(self.callsign)
        # Pre-generate channels to setup APRS properly
        _ = self.analog_aprs.channels(self.chan_seq)

        # Select EU or US APRS config based on region
        if self.aprs_region == "US":
            self.analog_aprs_config = self.analog_aprs.aprs_config_us(self.aprs_seq)
        else:  # Default to EU
            self.analog_aprs_config = self.analog_aprs.aprs_config_eu(self.aprs_seq)

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
