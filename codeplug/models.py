from utils import create_class_with_attributes

Contact = create_class_with_attributes(
    {"internal_id": int, "name": str, "calling_id": int}
)

GroupList = create_class_with_attributes(
    {"internal_id": int, "name": str, "contact_ids": list}
)

DigitalChannel = create_class_with_attributes(
    {
        "internal_id": int,
        "name": str,
        "rx_freq": float,
        "tx_freq": float,
        "tx_power": str,
        "scanlist_id": str,
        "tot": str,
        "rx_only": str,
        "admit_crit": str,
        "color": int,
        "slot": int,
        "rx_grouplist_id": str,
        "tx_contact_id": str,
        # Used for grouping
        "lat": float,
        "lng": float,
        "locator": str,
    }
)

AnalogChannel = create_class_with_attributes(
    {
        "internal_id": int,
        "name": str,
        "rx_freq": float,
        "tx_freq": float,
        "tx_power": str,
        "scanlist_id": str,
        "tot": str,
        "rx_only": str,
        "admit_crit": str,
        "squelch": str,
        "rx_tone": str,
        "tx_tone": str,
        "width": float,
        # Used for grouping
        "lat": float,
        "lng": float,
        "locator": str,
    }
)

Zone = create_class_with_attributes(
    {
        "internal_id": int,
        "name": str,
        "channels": list,
    }
)
