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
    def __init__(self, contact_gen, grouplist_gen, dmr_id, callsign):
        self.contact_gen = contact_gen
        self.grouplist_gen = grouplist_gen
        self.dmr_id = dmr_id
        self.callsign = callsign

    def generate(self, where):
        self.write_radio(where)
        self.write_contacts(where)
        self.write_grouplists(where)
        self.write_uid_and_name(where)

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
            print("%5d   %s %-7s %-8d %s" % (contact.internal_id, self._format_contact_name(contact.name), "Group", contact.calling_id, "-"), file=where)

        print("", file=where)

    def write_grouplists(self, where):
        print("Grouplist Name                              Contacts", file=where)
        for grouplist in self.grouplist_gen.grouplists():
            print("%5d   %s %s" % (grouplist.internal_id, self._format_contact_name(grouplist.name), self._format_contact_ids(grouplist.contact_ids)), file=where)

        print("", file=where)

    def write_digital_channels(self, where):
        print("Digital Name             Receive   Transmit Power Scan TOT RO Admit  Color Slot RxGL TxContact", file=where)
        for chan in self.digi_chan_gen.generate():
            pass

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
