# Distance Sorting Feature

## Overview

The distance sorting feature allows recipes to sort analog channels and zones by their distance from a reference location. This is particularly useful for prioritizing nearby repeaters and organizing your codeplug based on geographic proximity.

## Usage

### Command Line Interface

Distance sorting is automatically enabled for recipes that have a location configured:

```bash
python -m codeplug.cli output.csv CALLSIGN 1234567 usa
```

Arguments:
1. `output.csv` - Output filename
2. `CALLSIGN` - Your callsign
3. `1234567` - Your DMR ID
4. `usa` - Recipe name

### Configuring Location in Recipes

Each recipe can hardcode its own reference location for distance sorting. The location is set in the recipe's `__init__` method:

Example from `usa.py`:

```python
class Recipe(BaseRecipe):
    def __init__(self, callsign, dmr_id, filename, radio_class, writer_class):
        super().__init__(callsign, dmr_id, filename, radio_class, writer_class)
        # Set location for distance sorting (New York City)
        # Latitude, Longitude for NYC area
        self.location = (40.7128, -74.0060)

    def prepare(self):
        # ... rest of recipe code ...
        
        # Sort analog channels by distance if location is configured
        if self.location is not None:
            reference_lat, reference_lng = self.location
            analog_2m_channels = sort_channels_by_distance(
                analog_2m_channels, reference_lat, reference_lng
            )
```

To disable distance sorting for a recipe, simply set `self.location = None` or don't set it at all.

## API Reference

### `sort_channels_by_distance()`

Sorts a list of channels by distance from a reference point.

```python
from filters import sort_channels_by_distance

sorted_channels = sort_channels_by_distance(
    channels=channel_list,
    reference_lat=40.7128,
    reference_lng=-74.0060,
    channels_without_coordinates_last=True
)
```

**Parameters:**
- `channels` (List): List of channel objects to sort
- `reference_lat` (float): Reference latitude in decimal degrees
- `reference_lng` (float): Reference longitude in decimal degrees
- `channels_without_coordinates_last` (bool, optional): If `True` (default), channels without coordinates are placed at the end. If `False`, they're placed at the beginning.

**Returns:**
- List of channels sorted by distance from the reference point

**Behavior:**
- Channels are sorted by distance in ascending order (closest first)
- Channels without valid coordinates are grouped together at the end (or beginning)
- Uses the haversine formula to calculate great-circle distances
- Distance is calculated from the channel's `_lat` and `_lng` attributes

### `sort_zones_by_distance()`

Sorts a list of zones by the minimum distance of their channels from a reference point.

```python
from filters import sort_zones_by_distance

sorted_zones = sort_zones_by_distance(
    zones=zone_list,
    channels=all_channels,
    reference_lat=40.7128,
    reference_lng=-74.0060,
    zones_without_coordinates_last=True
)
```

**Parameters:**
- `zones` (List): List of zone objects to sort
- `channels` (List): List of all channel objects (needed to look up zone channels)
- `reference_lat` (float): Reference latitude in decimal degrees
- `reference_lng` (float): Reference longitude in decimal degrees
- `zones_without_coordinates_last` (bool, optional): If `True` (default), zones with no valid coordinates are placed at the end.

**Returns:**
- List of zones sorted by their minimum channel distance from the reference point

**Behavior:**
- Each zone's distance is determined by its **closest channel**
- Zones are sorted by this minimum distance in ascending order
- Zones without any channels with valid coordinates are grouped at the end (or beginning)
- The function creates a mapping of channel IDs to channel objects for efficient lookup

## Implementation Details

### Distance Calculation

The distance sorting functions use the haversine formula to calculate great-circle distances between two points on Earth. This provides accurate distance measurements accounting for the Earth's curvature.

Formula implementation in `filters.py`:
```python
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth.
    Returns distance in kilometers.
    """
    # Implementation converts decimal degrees to radians
    # and applies the haversine formula
    # Returns distance in kilometers
```

### Channel Coordinates

Channels must have `_lat` and `_lng` attributes containing their coordinates:
- `_lat`: Latitude in decimal degrees
- `_lng`: Longitude in decimal degrees

Channels without these attributes or with `None` values will be grouped separately.

### Zone Distance

Zones are sorted based on the **closest channel** within each zone. This means:
- A zone with channels at 10km, 50km, and 100km will be sorted based on the 10km distance
- A zone with all far channels will be sorted after zones with at least one close channel
- Empty zones or zones with no valid coordinates are placed last

## Examples

### Example 1: Sorting Analog Channels

```python
from filters import sort_channels_by_distance

# Generate channels (from various sources)
all_channels = analog_channel_generator.channels(chan_seq)

# Sort by distance if location is provided
if self.location is not None:
    reference_lat, reference_lng = self.location
    all_channels = sort_channels_by_distance(
        all_channels, reference_lat, reference_lng
    )
```

### Example 2: Sorting Zones

```python
from filters import sort_zones_by_distance

# Generate zones
zones = zone_aggregator.zones(zone_seq)

# Sort zones by distance if location is provided
if self.location is not None:
    reference_lat, reference_lng = self.location
    # Need all channels for zone distance calculation
    all_channels = self.digital_channels + self.analog_channels
    zones = sort_zones_by_distance(
        zones, all_channels, reference_lat, reference_lng
    )
```

### Example 3: Complete Recipe with Distance Sorting

```python
class Recipe(BaseRecipe):
    def prepare(self):
        # ... generate channels ...
        
        # Sort analog channels by distance if location is provided
        if self.location is not None:
            reference_lat, reference_lng = self.location
            analog_2m_channels = sort_channels_by_distance(
                analog_2m_channels, reference_lat, reference_lng
            )
            analog_70cm_channels = sort_channels_by_distance(
                analog_70cm_channels, reference_lat, reference_lng
            )
        
        # ... generate zones ...
        
        # Sort zones by distance if location is provided
        if self.location is not None:
            reference_lat, reference_lng = self.location
            all_channels = self.digital_channels + self.analog_channels
            zones = sort_zones_by_distance(
                zones, all_channels, reference_lat, reference_lng
            )
        
        self.zones = zones
```

## Benefits

1. **Prioritize Nearby Repeaters**: Channels are ordered by proximity, making it easier to find and access nearby repeaters
2. **Better Organization**: Zones are arranged based on their geographic location relative to you
3. **Flexible**: Works alongside existing filtering (e.g., band filters, distance filters)
4. **Optional**: If no location is provided, default ordering is preserved
5. **Robust**: Handles channels and zones without coordinates gracefully

## Testing

The implementation includes comprehensive tests in `tests/test_distance_sorting.py`:
- Basic channel sorting by distance
- Handling channels without coordinates
- Zone sorting based on closest channel
- Edge cases (empty zones, missing channels, etc.)

Run tests with:
```bash
poetry run pytest tests/test_distance_sorting.py -v
```

## Related Features

- **DistanceFilter**: Filters channels by maximum distance (in `filters.py`)
- **BandFilter**: Filters channels by frequency band
- **RegionFilter**: Filters channels by geographic bounding box

These filters can be combined with distance sorting for powerful codeplug customization.
