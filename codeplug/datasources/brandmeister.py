import os.path
import json
import requests

ContactDB = json.load(open("data/brandmeister_talkgroups.json"))


class API:
    def static_talkgroups(self, device_id):
        response_json = self.cached(device_id)
        if response_json is None:
            response = requests.get(
                f"https://api.brandmeister.network/v2/device/{device_id}/talkgroup"
            )
            self.write_cache(device_id, response)
            response_json = response.json()
        return [
            (int(entry["talkgroup"]), int(entry["slot"])) for entry in response_json
        ]

    def cached(self, device_id):
        filename = self.cache_key(device_id)
        if os.path.isfile(filename):
            return json.load(open(filename))
        else:
            return None

    def write_cache(self, device_id, response):
        filename = self.cache_key(device_id)
        with open(filename, "wt") as f:
            json.dump(response.json(), f)

    def cache_key(self, device_id):
        return f"cache/static_talkgroups/{device_id}.json"
