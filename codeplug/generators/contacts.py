import re
import json

from models import Contact
from datasources.brandmeister import ContactDB


class BrandmeisterTGContactGenerator:
    def __init__(self):
        self._contactdb = ContactDB
        self._contacts = []

    def contacts(self):
        if len(self._contacts) == 0:
            self.generate_contacts()
        return self._contacts

    def generate_contacts(self):
        i = 1
        for key in self._contactdb:
            self._contacts.append(
                Contact(
                    internal_id=i,
                    name=self._sanitize_contact(self._contactdb[key]),
                    calling_id=int(key),
                )
            )
            i += 1

    def _sanitize_contact(self, name):
        # NOTE: 13/06/2023 (jps): Some contact names contain newlines (!)
        return name.strip("\r\n")

    def prefixed_contacts(self, prefix):
        contacts = []
        for c in self.contacts():
            if str(c.calling_id).startswith(prefix):
                contacts.append(c)
        return contacts

    def matched_contacts(self, regex):
        contacts = []
        for c in self.contacts():
            if re.search(regex, str(c.calling_id)):
                contacts.append(c)
        return contacts
