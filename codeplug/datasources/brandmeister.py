import os.path
import json
from datetime import datetime, timedelta

import requests

from .cache import FileCache
from .ratelimit import RateLimiter

ContactDB = json.load(open("data/brandmeister_talkgroups.json"))
UnlistedContactDB = json.load(open("data_static/brandmeister_unlisted_talkgroups.json"))

# Shared by every Brandmeister client so the quota is tracked across them.
RATE_LIMITER = RateLimiter(min_interval=1.0)


class DeviceDB(FileCache):
    def __init__(self):
        FileCache.__init__(self, "bm_devices", rate_limiter=RATE_LIMITER)
        self.devices = self.cached(
            "repeaters",
            f"https://api.brandmeister.network/v2/device/?repeater=true",
        )

    def devices_by_callsign(self, callsign):
        """All devices registered under callsign, hotspots included."""
        return self.cached(
            f"bycall_{callsign.upper()}",
            f"https://api.brandmeister.network/v2/device/byCall?callsign={callsign}",
        )

    def devices_recently_active(self, days=30):
        return [
            d
            for d in self.devices
            if d["last_seen"]
            and datetime.now() - datetime.fromisoformat(d["last_seen"])
            < timedelta(days=days)
        ]


class TalkgroupAPI(FileCache):
    def __init__(self):
        FileCache.__init__(self, "static_talkgroups", rate_limiter=RATE_LIMITER)

    def static_talkgroups(self, device_id):
        response_json = self.cached(
            device_id,
            f"https://api.brandmeister.network/v2/device/{device_id}/talkgroup",
        )
        return [
            (int(entry["talkgroup"]), int(entry["slot"])) for entry in response_json
        ]
