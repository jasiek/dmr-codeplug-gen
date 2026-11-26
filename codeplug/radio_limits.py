"""
Per-radio capacity limits, and trimming of prepared codeplug data to fit them.

Limits are keyed by RADIO name. For most radios it is also the dmrconf radio
key (`dmrconf --list-radios`) that `make validate` checks against; a radio on
other firmware names its dmrconf model in `dmrconf` (see `dmrconf_command`).
AnyTone numbers come from qdmr's lib/<radio>_limits.cc and lib/<radio>_codeplug.hh.
"""

import sys
from dataclasses import dataclass, replace
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RadioLimits:
    name: str
    contacts: int
    grouplists: int
    grouplist_contacts: int
    channels: int  # analog + digital combined
    zones: int
    zone_channels: int
    scanlists: int
    scanlist_channels: int
    roaming_channels: int
    roaming_zones: int
    roaming_zone_channels: int
    dmrconf: Optional[str] = None  # dmrconf model when it isn't the RADIO key
    # Check with `dmrconf encode` instead of `verify`, for a model whose verify
    # is broken. encode checks parsing and references, not limits.
    dmrconf_encode: bool = False


_ANYTONE_878 = dict(
    contacts=10000,
    grouplists=250,
    grouplist_contacts=64,
    channels=4000,
    zones=250,
    zone_channels=250,
    scanlists=250,
    # qdmr's limits file says 31, but the codeplug scan list element has 50
    # member slots, matching the AnyTone CPS.
    scanlist_channels=50,
    roaming_channels=250,
    roaming_zones=64,
    roaming_zone_channels=64,
)

# Baofeng DM-32UV running RadioFoundry firmware. Its codeplug uses the
# open-firmware layout, which dmrconf's openuv380 model encodes (RadioFoundry
# docs/spec/qdmr-yaml.md 5), not the stock dm32uv one. dmrconf 0.15.1's
# `verify -R openuv380` segfaults on any file, so it is checked with encode.
# Numbers from RadioFoundry's core/codeplug/codeplug.h
# (CODEPLUG_*_MAX, CODEPLUG_ZONE_MAX, CODEPLUG_LIST_LEN). Its qdmr YAML import
# (docs/spec/qdmr-yaml.md) drops scan lists and roaming, so both are 0 here.
_RADIOFOUNDRY = dict(
    contacts=1024,
    grouplists=76,
    grouplist_contacts=32,
    channels=1024,
    zones=68,
    zone_channels=80,
    scanlists=0,
    scanlist_channels=0,
    roaming_channels=0,
    roaming_zones=0,
    roaming_zone_channels=0,
)

RADIOS: Dict[str, RadioLimits] = {
    "d878uv": RadioLimits(name="AT-D878UV", **_ANYTONE_878),
    "d878uv2": RadioLimits(name="AT-D878UVII", **_ANYTONE_878),
    "d578uv": RadioLimits(name="AT-D578UV", **_ANYTONE_878),
    "dm32uvrf": RadioLimits(
        name="DM-32UV (RadioFoundry)",
        dmrconf="openuv380",
        dmrconf_encode=True,
        **_RADIOFOUNDRY,
    ),
}

DEFAULT_RADIO = "d878uv"


def get_limits(radio: str) -> RadioLimits:
    try:
        return RADIOS[radio.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown radio '{radio}'. Supported: {', '.join(sorted(RADIOS))}"
        ) from None


def dmrconf_command(radio: str, plugfile: str) -> List[str]:
    """The dmrconf command line that checks a RADIO's codeplug file."""
    lim = get_limits(radio)
    model = lim.dmrconf or radio.lower()
    if lim.dmrconf_encode:
        binfile = plugfile.rsplit(".", 1)[0] + ".bin"
        return ["dmrconf", "-R", model, "-y", "encode", plugfile, binfile]
    return ["dmrconf", "-R", model, "-y", "verify", plugfile]


class CodeplugTrimmer:
    """
    Cuts prepared codeplug lists down to a radio's limits.

    Items are kept in their original order, so recipes control priority by
    ordering. References are fixed up after trimming: zones, scan lists,
    group lists and roaming zones only point at kept items, and channel
    references to dropped scan lists, group lists or contacts are cleared.
    """

    def __init__(self, limits: RadioLimits, out=sys.stderr):
        self.limits = limits
        self.out = out

    def report(self, what, before, after):
        if after < before:
            print(
                f"[{self.limits.name}] {what}: kept {after} of {before}",
                file=self.out,
            )

    def cap(self, what, items, limit):
        kept = list(items)[:limit]
        self.report(what, len(items), len(kept))
        return kept

    def trim(
        self,
        *,
        contacts,
        grouplists,
        analog_channels,
        digital_channels,
        zones,
        scanlists,
        roaming_channels,
        roaming_zones,
        analog_aprs_config,
        digital_aprs_config,
    ):
        lim = self.limits

        # Channels: APRS revert channel first, then zone order, then the rest.
        all_channels = list(analog_channels) + list(digital_channels)
        priority = []
        if analog_aprs_config:
            priority.append(analog_aprs_config.channel_id)
        for zone in zones:
            priority.extend(zone.channels)
        priority.extend(ch.internal_id for ch in all_channels)
        keep_channel_ids = set(list(dict.fromkeys(priority))[: lim.channels])
        self.report("channels", len(all_channels), len(keep_channel_ids))

        # Contacts: referenced ones first, then the rest.
        referenced = []
        if digital_aprs_config:
            referenced.append(digital_aprs_config.contact_id)
        for ch in digital_channels:
            if ch.internal_id in keep_channel_ids and ch.tx_contact_id:
                referenced.append(ch.tx_contact_id)
        for gl in grouplists:
            referenced.extend(gl.contact_ids)
        order = list(dict.fromkeys(referenced + [c.internal_id for c in contacts]))
        keep_contact_ids = set(order[: lim.contacts])
        kept_contacts = [c for c in contacts if c.internal_id in keep_contact_ids]
        self.report("contacts", len(contacts), len(kept_contacts))

        # Group lists
        kept_grouplists = []
        for gl in grouplists:
            ids = [cid for cid in gl.contact_ids if cid in keep_contact_ids]
            ids = self.cap(f"group list '{gl.name}'", ids, lim.grouplist_contacts)
            if ids:
                kept_grouplists.append(replace(gl, contact_ids=ids))
        kept_grouplists = self.cap("group lists", kept_grouplists, lim.grouplists)
        keep_grouplist_ids = {gl.internal_id for gl in kept_grouplists}

        # Zones
        kept_zones = []
        for zone in zones:
            ids = [cid for cid in zone.channels if cid in keep_channel_ids]
            ids = self.cap(f"zone '{zone.name}'", ids, lim.zone_channels)
            if ids:
                kept_zones.append(replace(zone, channels=ids))
        kept_zones = self.cap("zones", kept_zones, lim.zones)

        # Scan lists (a radio without them drops all, with one report line)
        kept_scanlists = []
        if not lim.scanlists:
            self.report("scan lists", len(scanlists), 0)
            scanlists = []
        for sl in scanlists:
            ids = [cid for cid in sl.channels if cid in keep_channel_ids]
            ids = self.cap(f"scan list '{sl.name}'", ids, lim.scanlist_channels)
            if ids:
                kept_scanlists.append(replace(sl, channels=ids))
        kept_scanlists = self.cap("scan lists", kept_scanlists, lim.scanlists)
        keep_scanlist_ids = {sl.internal_id for sl in kept_scanlists}

        # Channels, with dangling references cleared
        def fix_channel(ch, digital):
            changes = {}
            if ch.scanlist_id and ch.scanlist_id not in keep_scanlist_ids:
                changes["scanlist_id"] = None
            if digital:
                if ch.tx_contact_id and ch.tx_contact_id not in keep_contact_ids:
                    changes["tx_contact_id"] = None
                if (
                    ch.rx_grouplist_id
                    and ch.rx_grouplist_id != "-"
                    and ch.rx_grouplist_id not in keep_grouplist_ids
                ):
                    changes["rx_grouplist_id"] = None
            return replace(ch, **changes) if changes else ch

        kept_analog = [
            fix_channel(ch, False)
            for ch in analog_channels
            if ch.internal_id in keep_channel_ids
        ]
        kept_digital = [
            fix_channel(ch, True)
            for ch in digital_channels
            if ch.internal_id in keep_channel_ids
        ]

        # Roaming
        kept_roaming_channels = self.cap(
            "roaming channels", roaming_channels, lim.roaming_channels
        )
        keep_rch_ids = {ch.internal_id for ch in kept_roaming_channels}
        kept_roaming_zones = []
        if not lim.roaming_zones:
            self.report("roaming zones", len(roaming_zones), 0)
            roaming_zones = []
        for rz in roaming_zones:
            ids = [cid for cid in rz.channels if cid in keep_rch_ids]
            ids = self.cap(f"roaming zone '{rz.name}'", ids, lim.roaming_zone_channels)
            if ids:
                kept_roaming_zones.append(replace(rz, channels=ids))
        kept_roaming_zones = self.cap(
            "roaming zones", kept_roaming_zones, lim.roaming_zones
        )

        return dict(
            contacts=kept_contacts,
            grouplists=kept_grouplists,
            analog_channels=kept_analog,
            digital_channels=kept_digital,
            zones=kept_zones,
            scanlists=kept_scanlists,
            roaming_channels=kept_roaming_channels,
            roaming_zones=kept_roaming_zones,
            analog_aprs_config=analog_aprs_config,
            digital_aprs_config=digital_aprs_config,
        )


if __name__ == "__main__":
    # make validate: python codeplug/radio_limits.py <RADIO> <PLUGFILE>
    import subprocess

    cmd = dmrconf_command(sys.argv[1], sys.argv[2])
    print(" ".join(cmd), file=sys.stderr)
    sys.exit(subprocess.run(cmd).returncode)
