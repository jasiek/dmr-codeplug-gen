import sys
import json
from unidecode import unidecode

CONTACT_NAME_MAX = 16  # https://github.com/OpenRTX/dmrconfig/blob/master/d868uv.c#L317

# TODO:
#
# Digital channels
# Analog channels
# Zones
# Scanlists (low prio)
# Messages (low prio)
# Intro lines (low prio)


class Codeplug:
    def __init__(self, contact_gen, grouplist_gen, dmr_id, callsign, analog_chan_gen):
        self.contact_gen = contact_gen
        self.grouplist_gen = grouplist_gen
        self.dmr_id = dmr_id
        self.callsign = callsign
        self.analog_chan_gen = analog_chan_gen

    def generate(self, where):
        self.write_radio(where)
        self.write_contacts(where)
        self.write_grouplists(where)
        self.write_uid_and_name(where)
        self.write_analog_channels(where)

    def write_radio(self, where):
        print("Radio: Anytone AT-D878UV", file=where)
        print("", file=where)

    def write_uid_and_name(self, where):
        print(f"ID: {self.dmr_id}", file=where)
        print(f"Name: {self.callsign}", file=where)
        print("", file=where)

    def write_contacts(self, where):
        print("Contact Name             Type    ID       RxTone", file=where)
        for contact in self.contact_gen.contacts():
            print(
                "%5d   %s %-7s %-8d %s"
                % (
                    contact.internal_id,
                    self._format_contact_name(contact.name),
                    "Group",
                    contact.calling_id,
                    "-",
                ),
                file=where,
            )

        print("", file=where)

    def write_grouplists(self, where):
        print("Grouplist Name                              Contacts", file=where)
        for grouplist in self.grouplist_gen.grouplists():
            print(
                "%5d   %s %s"
                % (
                    grouplist.internal_id,
                    self._format_contact_name(grouplist.name),
                    self._format_contact_ids(grouplist.contact_ids),
                ),
                file=where,
            )

        print("", file=where)

    def write_digital_channels(self, where):
        print(
            "Digital Name             Receive   Transmit Power Scan TOT RO Admit  Color Slot RxGL TxContact",
            file=where,
        )
        for chan in self.digi_chan_gen.generate():
            print(
                "%5d   %s %3.4f %+1.4f %-5s %-4d %-3s %-2s %-5s"
                % (
                    chan.internal_id,
                    chan.name,
                    chan.rx_freq,
                    chan.tx_freq_or_offset,
                    chan.tx_power,
                    chan.scanlist_id,
                    "-",
                    chan.rx_only,
                    chan.admit_crit,
                ),
                file=where,
            )

    def write_analog_channels(self, where):
        print(
            "Analog  Name             Receive   Transmit Power Scan TOT RO Admit  Squelch RxTone TxTone Width",
            file=where,
        )
        for chan in self.analog_chan_gen.channels():
            print(
                "%5d   %-16s %3.4f  %+1.4f  %-5s %-4s %-3s %-2s %-6s %-7s %-6s %-6s %-5s"
                % (
                    chan.internal_id,
                    chan.name,
                    chan.rx_freq,
                    chan.tx_freq_or_offset,
                    chan.tx_power,
                    chan.scanlist_id,
                    chan.tot,
                    chan.rx_only,
                    chan.admit_crit,
                    chan.squelch,
                    chan.rx_tone,
                    chan.tx_tone,
                    chan.width,
                ),
                file=where,
            )
        print("", file=where)

    # private

    def _format_contact_name(self, name):
        # NOTE: 13/06/2023 (jps): Max size of contact name
        name = name[:CONTACT_NAME_MAX]
        # NOTE: 13/06/2023 (jps): Only ascii characters are permitted
        name = unidecode(name)
        return name.ljust(CONTACT_NAME_MAX).replace(" ", "_")

    def _format_contact_ids(self, contact_ids):
        ranges = []
        start = contact_ids[0]
        end = contact_ids[0]

        for i in range(1, len(contact_ids)):
            if contact_ids[i] - contact_ids[i - 1] == 1:
                end = contact_ids[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(str(start) + "-" + str(end))
                start = contact_ids[i]
                end = contact_ids[i]

        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(str(start) + "-" + str(end))

        return ",".join(ranges)
