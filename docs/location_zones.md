# Location-Based Zone Generators

The DMR codeplug generator now includes powerful location-based zone clustering capabilities that can group repeaters by geographical proximity using GPS coordinates.

## Overview

Two new zone generators are available:

### 1. LocationClusterZoneGenerator
Groups repeaters that are within a specified distance threshold into the same zone, creating geographical clusters.

### 2. DistanceBandedZoneGenerator  
Creates zones based on distance bands from a reference point (like "Local", "Regional", "Distant").

## LocationClusterZoneGenerator

This generator uses a greedy distance-based clustering algorithm to group nearby repeaters together.

### Features

- **Distance-based clustering**: Groups repeaters within a maximum distance threshold
- **Minimum cluster size**: Only creates zones with sufficient repeaters
- **Flexible naming strategies**: Three ways to name clusters:
  - `representative`: Uses the first/most central repeater's callsign
  - `centroid`: Uses the geographic center of the cluster  
  - `center`: Uses the repeater closest to the geographic center
- **QTH inclusion**: Optionally includes location information in zone names

### Usage Example

```python
from generators.location_zones import LocationClusterZoneGenerator

# Create a zone generator that clusters repeaters within 25km
generator = LocationClusterZoneGenerator(
    channels=all_channels,
    max_distance_km=25.0,           # Maximum distance between repeaters in same zone
    min_repeaters_per_zone=2,       # Minimum repeaters required per zone
    zone_naming="representative",   # How to name zones
    include_qth_in_name=True        # Include location info in zone names
)

# Generate zones
zones = generator.zones(sequence)
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channels` | List | Required | List of channels to cluster |
| `max_distance_km` | float | 25.0 | Maximum distance in km between repeaters in same cluster |
| `min_repeaters_per_zone` | int | 2 | Minimum repeaters required to form a zone |
| `zone_naming` | str | "representative" | How to name zones: "representative", "centroid", or "center" |
| `include_qth_in_name` | bool | True | Whether to include QTH information in zone names |

## DistanceBandedZoneGenerator

This generator sorts repeaters into zones based on their distance from a reference point.

### Features

- **Distance bands**: Define custom distance ranges for zones
- **Reference point**: Use any GPS coordinate as the reference
- **Automatic categorization**: Channels are automatically placed in the appropriate distance band

### Usage Example

```python
from generators.location_zones import DistanceBandedZoneGenerator

# Create a zone generator for distance bands from NYC
generator = DistanceBandedZoneGenerator(
    channels=all_channels,
    reference_lat=40.7128,    # NYC latitude
    reference_lon=-74.0060,   # NYC longitude
    distance_bands=[
        ("Local", 0, 100),      # 0-100km
        ("Regional", 100, 200), # 100-200km  
        ("Distant", 200, 500),  # 200-500km
    ],
    include_qth_in_name=True
)

# Generate zones
zones = generator.zones(sequence)
```

### Configuration Options

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channels` | List | Yes | List of channels to zone |
| `reference_lat` | float | Yes | Reference latitude for distance calculations |
| `reference_lon` | float | Yes | Reference longitude for distance calculations |
| `distance_bands` | List[Tuple[str,float,float]] | Yes | List of (name, min_km, max_km) tuples |
| `include_qth_in_name` | bool | No | Whether to include QTH information in zone names |

## Integration with Recipes

Here's how to add location-based zones to an existing recipe:

### Example: Adding Location Clustering to USA Recipe

```python
# In your recipe's prepare_zones() method:
def prepare_zones(self):
    """Prepare channel zones with location-based clustering."""
    
    # Create location-based zones from analog channels
    location_cluster_gen = LocationClusterZoneGenerator(
        channels=self.analog_channels,
        max_distance_km=25.0,
        min_repeaters_per_zone=2,
        zone_naming="representative"
    )
    
    # Traditional callsign-based zones for digital channels
    callsign_gen = ZoneFromCallsignGenerator2(self.digital_channels)
    
    zones = ZoneAggregator(
        HotspotZoneGenerator(self.digital_channels),
        location_cluster_gen,  # New location-based zones
        callsign_gen,          # Traditional zones
    ).zones(self.zone_seq)
    
    self.zones = zones
```

### Example: Using Distance Bands from Your QTH

```python
def prepare_zones(self):
    """Prepare zones based on distance from your location."""
    
    if self.location is None:
        # Fallback if no location is set
        self.location = (40.7128, -74.0060)  # NYC default
    
    lat, lon = self.location
    
    # Create distance-banded zones
    distance_bands = [
        ("Local", 0, 50),       # Within 50km
        ("Regional", 50, 150),  # 50-150km
        ("Distant", 150, 300),  # 150-300km
        ("Far", 300, 500),      # 300-500km
    ]
    
    location_zone_gen = DistanceBandedZoneGenerator(
        channels=self.analog_channels,
        reference_lat=lat,
        reference_lon=lon,
        distance_bands=distance_bands
    )
    
    zones = ZoneAggregator(
        location_zone_gen,
        HotspotZoneGenerator(self.digital_channels)
    ).zones(self.zone_seq)
    
    self.zones = zones
```

## Distance Calculation

Both generators use the Haversine formula to calculate the great-circle distance between two GPS coordinates, accounting for the Earth's curvature:

```python
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    return c * 6371
```

## Best Practices

### LocationClusterZoneGenerator
- Use `max_distance_km=25.0` for urban areas with dense repeaters
- Use `max_distance_km=50-100` for rural areas with sparse repeaters  
- Set `min_repeaters_per_zone=2-3` to avoid single-repeater zones
- Use `zone_naming="representative"` for callsign-based naming

### DistanceBandedZoneGenerator
- Choose distance bands that make sense for your usage patterns
- Use your actual location as the reference point for personal usage
- Consider overlapping bands if you want some repeaters in multiple zones
- Test different reference points to see what works best for your area

## Error Handling

Both generators handle edge cases gracefully:

- Channels without location data are automatically excluded
- Clusters below minimum size are discarded
- Empty zone lists are returned with informative messages
- Distance calculations handle edge cases like same coordinates

## Performance

The clustering algorithm has O(n²) complexity in the worst case, but:
- Uses efficient filtering for channels without location data
- Employs a greedy approach that terminates early for small clusters
- Is optimized for typical amateur radio repeater densities (tens to hundreds of repeaters)

For most practical use cases with hundreds of repeaters, zone generation completes in milliseconds.
