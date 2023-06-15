import sys
import json
from unidecode import unidecode
from prettytable import PrettyTable, PLAIN_COLUMNS

CONTACT_NAME_MAX = 16  # https://github.com/OpenRTX/dmrconfig/blob/master/d868uv.c#L317


class Codeplug:
    def __init__(self, contact_gen):
        self.contact_gen = contact_gen

    def generate(self, where):
        self.write_radio(where)
        self.write_contacts(where)

    def write_radio(self, where):
        print("Radio: Anytone AT-D878UV", file=where)

    def write_contacts(self, where):
        t = PrettyTable(["Contact", "Name", "Type", "ID", "RxTone"])
        t.set_style(PLAIN_COLUMNS)
        t.align = "l"
        for contact in self.contact_gen.contacts():
            t.add_row(
                [
                    contact.internal_id,
                    self._format_contact_name(contact.name),
                    "Group",
                    contact.calling_id,
                    "-",
                ]
            )

        print(t.get_string(sortby="Contact", file=where))

    def _format_contact_name(self, name):
        # NOTE: 13/06/2023 (jps): Max size of contact name
        name = name[:CONTACT_NAME_MAX]
        # NOTE: 13/06/2023 (jps): Only ascii characters are permitted
        name = unidecode(name)
        return name
