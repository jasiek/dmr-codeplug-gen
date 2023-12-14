from utils import create_class_with_attributes

Contact = create_class_with_attributes(
    {"internal_id": int, "name": str, "calling_id": int}
)

GroupList = create_class_with_attributes(
    {"internal_id": int, "name": str, "contact_ids": list}
)

AnalogChannel = create_class_with_attributes(
    {
        "internal_id": int,
        "name": str,
        "rx_freq": float,
        "tx_freq_or_offset": float,
        "tx_power": str,
        "scanlist_id": str,
        "tot": str,
        "rx_only": str,
        "admit_crit": str,
        "squelch": str,
        "rx_tone": str,
        "tx_tone": str,
        "width": float,
    }
)
