import json
from models import Contact, GroupList


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


class CountryGroupListGenerator:
    # Group groups by country, if possible
    def __init__(self, contacts, country_id):
        self._contacts = contacts
        self._country_id = str(country_id)

    def grouplists(self):
        matching_ids = [
            contact.internal_id
            for contact in self._contacts
            if str(contact.calling_id).startswith(self._country_id)
        ]
        i = 1
        yield GroupList(internal_id=i, name="Poland", contact_ids=matching_ids)
