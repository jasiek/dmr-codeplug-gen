import os.path
import json
from datetime import datetime, timedelta

import requests

from .cache import FileCache

ContactDB = json.load(open("data/brandmeister_talkgroups.json"))


class DeviceDB(FileCache):
    def __init__(self, master=2602):
        FileCache.__init__(self, "bm_devices")
        self.master = 2602
        self.devices = self.cached(
            str(self.master),
            f"https://api.brandmeister.network/v2/device/byMaster/{self.master}",
        )

    def devices_active_within1month(self):
        return [
            d
            for d in self.devices
            if d["last_seen"]
            and datetime.now() - datetime.fromisoformat(d["last_seen"])
            < timedelta(days=30)
        ]


class TalkgroupAPI(FileCache):
    def __init__(self):
        FileCache.__init__(self, "static_talkgroups")

    def static_talkgroups(self, device_id):
        response_json = self.cached(
            device_id,
            f"https://api.brandmeister.network/v2/device/{device_id}/talkgroup",
        )
        return [
            (int(entry["talkgroup"]), int(entry["slot"])) for entry in response_json
        ]
