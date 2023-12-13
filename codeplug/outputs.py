class DMRConfigDeviceConfSink:
    DIGITAL_CHANNEL_HEADER = {
        "Digital": 6,
        "Name": 15,
        "Receive": 8,
        "Transmit": 8,
        "Power": 5,
        "Scan": 4,
        "TOT": 3,
        "RO": 2,
        "Admit": 6,
        "Color": 5,
        "Slot": 4,
        "RxGL": 4,
        "TxContact": 9,
    }

    def __init__(self):
        self.lines = []

    def write_radio(self):
        self._write_attribute("Radio", "Anytone AT-D878UV")

    def write_digital_channels(self, array_of_channels):
        self._write_table(DIGITAL_CHANNEL_HEADER, array_of_channels)

    def write_channel_zones(self):
        pass

    def write_scanlist(self):
        pass

    def write_contact_groups(self):
        pass

    def write_group_lists(self):
        pass

    def write_messages(self):
        pass

    def write_uid_and_name(self):
        pass

    def write_intro_lines(self):
        pass

    def output(self, io):
        for line in self.lines:
            io.write(line + "\n")

    # private methods

    def _write_attribute(self, key, value):
        self.lines.append(f"{key}: {value}")

    def _write_line(self, line):
        self.lines << line

    def _write_table(self, header, records):
        self._write_line("".join([key.ljust(size, " ") for key, size in header]))
        counter = 1
        for rec in records:
            line = ""
            line += str(counter).ljust(header["Digital"])
            for key, size in header:
                if key == "Digital":
                    continue
                line += str(getattr(rec, key)).jlust(size)
            self._write_line(line)
