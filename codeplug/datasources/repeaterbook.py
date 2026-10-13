from urllib.parse import urlencode

from .cache import FileCache
from .przemienniki import LXMLCacheAdapter


class RepeaterBookAPI(FileCache):
    """
    RepeaterBook data served by api.codeplug.org

    The API mirrors RepeaterBook and returns RXF XML in the "radio"
    perspective: qrg/ctcss type="rx" is what the radio receives and
    type="tx" is what the radio transmits.
    """

    base_url = "https://api.codeplug.org/repeaterbook"

    def __init__(self):
        FileCache.__init__(self, "repeaterbook", LXMLCacheAdapter())

    def repeaters_near(self, lat, lng, range_km, modes=("fm",)):
        """
        Get working repeaters within range_km of (lat, lng)

        Args:
            lat: Reference latitude in decimal degrees
            lng: Reference longitude in decimal degrees
            range_km: Great-circle search radius in kilometres
            modes: RXF mode names, e.g. ("fm",) or ("dmr", "fusion")
        """
        params = {
            "latitude": lat,
            "longitude": lng,
            "range": range_km,
            "mode": ",".join(modes),
            "onlyworking": 1,
        }
        key = "_".join(f"{k}={v}" for k, v in params.items())
        return self.cached(key, f"{self.base_url}?{urlencode(params)}")
