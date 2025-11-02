from collections import defaultdict
from models import GroupList, ContactType
from datasources import brandmeister


class RXGroupListGenerator:
    """
    Generate RX Group Lists based on channel definitions and their talkgroups.

    According to the qdmr manual, a group list collects several digital (DMR) contacts
    that should be received on a channel. This generator:

    1. Groups channels by repeater callsign
    2. For each repeater, fetches all static talkgroups configured on it from Brandmeister API
    3. Creates an RXGroupList containing all available contacts/TGs for that repeater
    4. Updates channels to reference the appropriate RXGroupList

    This allows the radio to receive any of the static talkgroups configured on a repeater,
    not just the one set as the TX contact.
    """

    def __init__(self, channels, contacts):
        """
        Initialize the RXGroupList generator.

        Args:
            channels: List of DigitalChannel objects
            contacts: List of Contact objects (talkgroups)
        """
        self._channels = channels
        self._contacts = contacts
        self._grouplists = []
        self._repeater_to_grouplist = {}  # Maps repeater callsign to grouplist_id

        # Create a mapping from calling_id to contact internal_id for quick lookup
        self._calling_id_to_contact = {
            contact.calling_id: contact for contact in contacts
        }

    def grouplists(self, sequence):
        """
        Generate RXGroupLists and update channels with the appropriate grouplist_id.

        Args:
            sequence: Sequence generator for internal IDs

        Returns:
            List of GroupList objects
        """
        if len(self._grouplists) > 0:
            return self._grouplists

        # Group channels by repeater callsign
        repeater_channels = defaultdict(list)
        for channel in self._channels:
            # Skip hotspot channels and channels without a repeater callsign
            if channel._rpt_callsign and not channel.name.startswith("HS"):
                repeater_channels[channel._rpt_callsign].append(channel)

        # Get Brandmeister device database
        device_db = brandmeister.DeviceDB()
        talkgroup_api = brandmeister.TalkgroupAPI()

        # Create a mapping from callsign to device ID
        callsign_to_device = {dev["callsign"]: dev["id"] for dev in device_db.devices}

        # For each repeater, create an RXGroupList
        for repeater_callsign, channels in repeater_channels.items():
            # Get the device ID for this repeater
            device_id = callsign_to_device.get(repeater_callsign)
            if not device_id:
                # Skip if we can't find the device
                continue

            # Fetch static talkgroups for this repeater
            try:
                static_tgs = talkgroup_api.static_talkgroups(device_id)
            except Exception:
                # Skip if we can't fetch talkgroups
                continue

            # Collect contact IDs for talkgroups that exist in our contact list
            # Only include GroupCall type contacts (exclude PrivateCall, AllCall)
            contact_ids = []
            for tg_id, slot in static_tgs:
                if tg_id in self._calling_id_to_contact:
                    contact = self._calling_id_to_contact[tg_id]
                    if (
                        contact.type == ContactType.GroupCall
                        and contact.internal_id not in contact_ids
                    ):
                        contact_ids.append(contact.internal_id)

            # Limit to 64 contacts per group list (hardware limitation)
            contact_ids = contact_ids[:64]

            # Only create a grouplist if we have contacts
            if contact_ids:
                grouplist_id = sequence.next()
                grouplist = GroupList(
                    internal_id=grouplist_id,
                    name=f"RX {repeater_callsign}",
                    contact_ids=contact_ids,
                )
                self._grouplists.append(grouplist)
                self._repeater_to_grouplist[repeater_callsign] = grouplist_id

                # Update all channels for this repeater with the grouplist_id
                for channel in channels:
                    channel.rx_grouplist_id = grouplist_id

        return self._grouplists


class HotspotRXGroupListGenerator:
    """
    Generate a single RX Group List for hotspot channels.

    Hotspots typically allow access to any talkgroup, so this generator
    creates one comprehensive grouplist containing all provided talkgroups.
    """

    def __init__(self, hotspot_channels, contacts):
        """
        Initialize the hotspot RXGroupList generator.

        Args:
            hotspot_channels: List of DigitalChannel objects for hotspots
            contacts: List of Contact objects (talkgroups) to include
        """
        self._channels = hotspot_channels
        self._contacts = contacts
        self._grouplists = []

    def grouplists(self, sequence):
        """
        Generate a single RXGroupList for all hotspot channels.

        Args:
            sequence: Sequence generator for internal IDs

        Returns:
            List containing a single GroupList object
        """
        if len(self._grouplists) > 0:
            return self._grouplists

        # Get all contact IDs, but only include GroupCall type contacts
        # Exclude PrivateCall and AllCall types (e.g., DMR APRS, PARROT)
        contact_ids = [
            contact.internal_id
            for contact in self._contacts
            if contact.type == ContactType.GroupCall
        ]

        # Limit to 64 contacts per group list (hardware limitation)
        contact_ids = contact_ids[:64]

        if contact_ids:
            grouplist_id = sequence.next()
            grouplist = GroupList(
                internal_id=grouplist_id, name="RX Hotspot", contact_ids=contact_ids
            )
            self._grouplists.append(grouplist)

            # Update all hotspot channels with this grouplist_id
            for channel in self._channels:
                if channel.name.startswith("HS"):
                    channel.rx_grouplist_id = grouplist_id

        return self._grouplists
