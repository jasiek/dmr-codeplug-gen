import copy
import os
from urllib.parse import urlencode

from lxml import etree

from .cache import FileCache
from .przemienniki import LXMLCacheAdapter


class RepeaterBookAPI(FileCache):
    """
    RepeaterBook data served by api.webchirp.org

    The API mirrors RepeaterBook and returns RXF XML in the "radio"
    perspective: qrg/ctcss type="rx" is what the radio receives and
    type="tx" is what the radio transmits.
    """

    base_url = "https://api.webchirp.org/repeaterbook"

    def __init__(self):
        FileCache.__init__(self, "repeaterbook", LXMLCacheAdapter())

    def request_headers(self):
        """
        Bearer auth from TURNSTILE_BYPASS_TOKEN

        The API otherwise answers 403 "Turnstile token required" to
        non-browser clients. Read per request so it is only needed when
        the cache misses.
        """
        token = os.environ.get("TURNSTILE_BYPASS_TOKEN")
        return {"Authorization": f"Bearer {token}"} if token else {}

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

    def repeaters_near_any(self, circles, modes=("fm",)):
        """
        Merge repeaters_near() results for several (lat, lng, range_km) circles

        Repeaters returned by more than one query are kept once, keyed by
        their RepeaterBook id.
        """
        return merge_rxf(
            *(self.repeaters_near(lat, lng, r, modes=modes) for lat, lng, r in circles)
        )


def merge_rxf(*roots):
    """
    Combine RXF roots into a new root, keeping each repeater once

    RepeaterBook ids are only unique within a state (NY #22 and NJ #22 are
    different repeaters), so repeaters are keyed on (state, id).
    """
    merged = etree.Element("rxf")
    container = etree.SubElement(merged, "repeaters")
    seen = set()
    for root in roots:
        for node in root.findall("repeaters/repeater"):
            repeater_id = node.findtext("id")
            key = (
                (qth_state_county(node)[0], repeater_id)
                if repeater_id
                else etree.tostring(node)
            )
            if key in seen:
                continue
            seen.add(key)
            container.append(copy.deepcopy(node))
    return merged


US_STATES = {
    "Connecticut",
    "New Jersey",
    "New York",
    "Pennsylvania",
    "Massachusetts",
    "Rhode Island",
    "Vermont",
    "Delaware",
    "Maryland",
}


def qth_state_county(node):
    """
    (state, county) parsed from a RepeaterBook qth of "City, State[, County]"

    The state is located by name rather than position, since some cities
    contain commas ("Mt Olive, Twp, New Jersey, Morris"). Either part is
    None when missing.
    """
    parts = [p.strip() for p in (node.findtext("qth") or "").split(",")]
    for i, part in enumerate(parts):
        if part in US_STATES:
            county = parts[i + 1] if i + 1 < len(parts) and parts[i + 1] else None
            return part, county
    return None, None


def split_rxf(root, key):
    """
    Partition an RXF root by key(node), returning {key: new RXF root}

    Every repeater lands in exactly one partition; the source is left untouched.
    """
    parts = {}
    for node in root.findall("repeaters/repeater"):
        name = key(node)
        if name not in parts:
            parts[name] = etree.Element("rxf")
            etree.SubElement(parts[name], "repeaters")
        parts[name].find("repeaters").append(copy.deepcopy(node))
    return parts
