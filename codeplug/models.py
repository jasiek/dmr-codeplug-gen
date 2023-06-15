class Contact:
    def __init__(self, internal_id, name, calling_id):
        self.internal_id = internal_id
        self.name = name
        self.calling_id = calling_id


class GroupList:
    def __init__(self, internal_id, name, contact_ids):
        self.internal_id = internal_id
        self.name = name
        self.contact_ids = contact_ids
