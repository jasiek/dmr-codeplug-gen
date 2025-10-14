import re
import json

from models import Contact, ContactType
from datasources.brandmeister import ContactDB


class BrandmeisterTGContactGenerator:
    def __init__(self):
        self._contactdb = ContactDB
        self._contacts = []

    def contacts(self, sequence):
        if len(self._contacts) == 0:
            self.generate_contacts(sequence)
        return self._contacts

    def generate_contacts(self, sequence):
        for key in self._contactdb:
            self._contacts.append(
                Contact(
                    internal_id=sequence.next(),
                    name=self._contactdb[key],
                    type=ContactType.GroupCall,
                    calling_id=int(key),
                )
            )

    def _sanitize_contact(self, name):
        # NOTE: 13/06/2023 (jps): Some contact names contain newlines (!)
        return name.strip("\r\n")

    def prefixed_contacts(self, prefix):
        contacts = []
        for c in self._contacts:
            if str(c.calling_id).startswith(prefix):
                contacts.append(c)
        return contacts

    def matched_contacts(self, regex):
        contacts = []
        for c in self._contacts:
            if re.search(regex, str(c.calling_id)):
                contacts.append(c)
        return contacts


class BrandmeisterSpecialContactGenerator:
    def __init__(self):
        self._contacts = []

    def contacts(self, sequence):
        if len(self._contacts) == 0:
            private = [
                ("262993 WX SMS", 262993),
                ("262994 RPT SMS", 262994),
                ("262995 SMSC", 262995),
                ("262997 PARROT", 262997),
            ]
            output = [
                Contact(
                    internal_id=sequence.next(),
                    name=d[0],
                    type=ContactType.PrivateCall,
                    calling_id=d[1],
                )
                for d in private
            ]

            tgs = [
                ("Disconnect", 4000),
                ("OARC M0OUK", 2348479),
            ]
            output += [
                Contact(
                    internal_id=sequence.next(),
                    name=d[0],
                    type=ContactType.GroupCall,
                    calling_id=d[1],
                )
                for d in tgs
            ]

        self._contacts = output
        return self._contacts

    def parrot(self):
        for c in self._contacts:
            if c.calling_id == 262997:
                return c
        return None

    def smsc(self):
        for c in self._contacts:
            if c.calling_id == 262995:
                return c
        return None


class APRSContactGenerator:
    def __init__(self):
        self._contacts = []

    def contacts(self, seq):
        if self._contacts == []:
            self._contacts = [
                Contact(
                    internal_id=seq.next(),
                    name="DMR APRS",
                    type=ContactType.PrivateCall,
                    calling_id=262999,
                )
            ]
        return self._contacts
