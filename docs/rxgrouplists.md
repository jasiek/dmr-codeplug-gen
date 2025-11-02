# RX Group Lists

## Overview

RX Group Lists define which digital (DMR) contacts (talkgroups) can be received on a channel. According to the qdmr manual specification, a group list collects several digital contacts that should be received on an associated channel.

## Implementation

The RXGroupList generators create group lists based on channel definitions and their configured talkgroups:

### RXGroupListGenerator

Creates repeater-specific RX Group Lists by:

1. Grouping channels by repeater callsign
2. Fetching all static talkgroups configured on each repeater from the Brandmeister API
3. Creating an RXGroupList containing all available contacts/TGs for that repeater
4. Automatically updating channels to reference the appropriate RXGroupList

This allows the radio to receive any of the static talkgroups configured on a repeater, not just the one set as the TX contact.

**Example:**
```python
from codeplug.generators.rxgrouplists import RXGroupListGenerator

# Generate RXGroupLists for repeater channels
repeater_rxgrouplists = RXGroupListGenerator(
    repeater_channels, 
    contacts
).grouplists(sequence)
```

### HotspotRXGroupListGenerator

Creates a single comprehensive RX Group List for hotspot channels containing all provided talkgroups. Hotspots typically allow access to any talkgroup, so this generator provides one list with all available contacts.

**Example:**
```python
from codeplug.generators.rxgrouplists import HotspotRXGroupListGenerator

# Generate RXGroupList for hotspot channels  
hotspot_rxgrouplists = HotspotRXGroupListGenerator(
    hotspot_channels,
    contacts
).grouplists(sequence)
```

## Usage in Recipes

The generators are typically used in the `prepare_grouplists()` method of a recipe:

```python
def prepare_grouplists(self):
    """
    Prepare RX Group Lists based on channel definitions and their talkgroups.
    """
    # Separate hotspot channels from repeater channels
    hotspot_channels = [
        ch for ch in self.digital_channels if ch.name.startswith("HS")
    ]
    repeater_channels = [
        ch for ch in self.digital_channels if not ch.name.startswith("HS")
    ]
    
    # Generate RXGroupLists for repeater channels
    repeater_rxgrouplists = RXGroupListGenerator(
        repeater_channels, self.contacts
    ).grouplists(Sequence())
    
    # Generate RXGroupList for hotspot channels
    hotspot_rxgrouplists = HotspotRXGroupListGenerator(
        hotspot_channels, self.contacts
    ).grouplists(Sequence())
    
    # Combine all group lists
    self.grouplists = repeater_rxgrouplists + hotspot_rxgrouplists
```

## Benefits

1. **Automatic RX Configuration**: Channels are automatically configured to receive all relevant talkgroups
2. **Repeater-Aware**: Each repeater gets a customized list based on its actual configuration
3. **API Integration**: Leverages Brandmeister API to get current static talkgroup assignments
4. **Flexible**: Separate handling for hotspots vs. repeaters

## Technical Details

### Data Flow

1. Channels are passed to the generator along with all available contacts
2. Generator groups channels by repeater callsign (or identifies hotspot channels)
3. For each repeater:
   - Looks up the repeater in the Brandmeister device database
   - Fetches static talkgroups via Brandmeister API
   - Creates a GroupList with matching contacts
   - Updates channel `rx_grouplist_id` fields
4. Returns list of generated GroupList objects

### Channel Updates

The generators automatically update the `rx_grouplist_id` field on channels to reference the appropriate group list. This happens during the `grouplists()` method call, so channels must be passed before being finalized.

### Error Handling

The RXGroupListGenerator gracefully handles:
- Repeaters not found in Brandmeister database (skips silently)
- API errors when fetching talkgroups (skips that repeater)
- Talkgroups that don't exist in the contacts list (filters them out)

## Testing

Tests are provided in `tests/test_rxgrouplists.py` covering:
- Hotspot group list generation
- Repeater group list generation
- Proper filtering of hotspot vs. repeater channels
- Channel updates with correct grouplist IDs

Run tests with:
```bash
python -m pytest tests/test_rxgrouplists.py -v
