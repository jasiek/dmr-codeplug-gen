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
        self.devices = self.cached(str(self.master))
        if self.devices is None:
            response = requests.get(
                f"https://api.brandmeister.network/v2/device/byMaster/{self.master}"
            )
            response_json = response.json()
            self.write_cache(str(self.master), response_json)
            self.devices = response_json

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
        response_json = self.cached(device_id)
        if response_json is None:
            response = requests.get(
                f"https://api.brandmeister.network/v2/device/{device_id}/talkgroup"
            )
            response_json = response.json()
            self.write_cache(device_id, response_json)
        return [
            (int(entry["talkgroup"]), int(entry["slot"])) for entry in response_json
        ]
