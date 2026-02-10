from models import ContactID, GroupListID, ChannelID, ZoneID, ScanListID, Slot


def fmt_contact_id(id: ContactID) -> str:
    return f"contact{id}"


def fmt_grouplist_id(id: GroupListID) -> str:
    return f"grouplist{id}"


def fmt_scanlist_id(id: ScanListID) -> str:
    return f"scanlist{id}"


def fmt_chan_id(id: ChannelID) -> str:
    return f"ch{id}"


def fmt_zone_id(id: ZoneID) -> str:
    return f"zone{id}"


def fmt_rzone_id(id: ZoneID) -> str:
    return f"roamingzone{id}"


def fmt_rchan_id(id: ChannelID) -> str:
    return f"roamingch{id}"


def fmt_ts(ts: Slot) -> str:
    return f"TS{ts}"


def fmt_aprs(id: ChannelID) -> str:
    return f"aprs{id}"


def fmt_contact_name(name: str) -> str:
    # Sanitize contact name to be compatible with codeplug requirements
    # For example, remove or replace unsupported characters, limit length, etc.
    return name.strip()[:16].strip()  # Limit to 16 characters
