import json

from models import Contact


class BrandmeisterTGContactGenerator:
    def __init__(self):
        self._contacts = json.load(open("data/brandmeister_talkgroups.json"))

    def contacts(self):
        i = 1
        for key in self._contacts:
            yield Contact(
                internal_id=i,
                name=self._sanitize_contact(self._contacts[key]),
                calling_id=int(key),
            )
            i += 1

    def _sanitize_contact(self, name):
        # NOTE: 13/06/2023 (jps): Some contact names contain newlines (!)
        return name.strip("\r\n")

    def prefixed_contacts(self, prefix):
        for c in self.contacts():
            if str(c.calling_id).startswith(prefix):
                yield c
