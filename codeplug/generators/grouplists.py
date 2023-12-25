from models import GroupList


class CountryGroupListGenerator:
    # Group groups by country, if possible
    def __init__(self, contacts, country_id):
        self._contacts = contacts
        self._country_id = str(country_id)

    def grouplists(self, sequence):
        matching_ids = [
            contact.internal_id
            for contact in self._contacts
            if str(contact.calling_id).startswith(self._country_id)
        ]
        yield GroupList(
            internal_id=sequence.next(), name="Poland", contact_ids=matching_ids
        )
