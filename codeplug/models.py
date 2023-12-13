from utils import create_class_with_attributes

Contact = create_class_with_attributes(
    {"internal_id": int, "name": str, "calling_id": int}
)

GroupList = create_class_with_attributes(
    {"internal_id": int, "name": str, "contact_ids": list}
)

DigitalChannel = create_class_with_attributes(
    {
        "Name": str,
        "Receive": str,
        "Transmit": str,
        "Power": str,
        "Scan": int,
        "TOT": None,
        "RO": str,
        "Admit": str,
        "Color": int,
        "Slot": int,
        "RxGL": int,
        "TxContact": int,
    }
)
