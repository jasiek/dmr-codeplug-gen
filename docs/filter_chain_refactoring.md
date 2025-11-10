# Filter Chain Refactoring

## Overview

The filter system has been refactored to use a filter chain architecture where filters are passed INTO generators rather than wrapping them. This ensures that only channels/zones that pass all filters receive sequence IDs, eliminating gaps in the ID sequence.

## Key Changes

### 1. New FilterChain Class

Filters are now organized into chains that can be passed to generators:

```python
from filters import FilterChain, DistanceFilter, BandFilter

# Create a filter chain
filter_chain = FilterChain([
    DistanceFilter(
        reference_lat=37.4852,
        reference_lng=-122.2364,
        max_distance_km=50.0
    ),
    BandFilter()  # Default 2m and 70cm bands
])
```

### 2. Updated Filter Classes

Filters now inherit from `BaseFilter` and implement `should_include(item)`:

- **DistanceFilter**: Tests if an item is within a specified distance from a reference point
- **RegionFilter**: Tests if an item is within geographic bounds
- **BandFilter**: Tests if a channel is within specified frequency bands

### 3. Generator Integration

Generators now accept an optional `filter_chain` parameter:

```python
# Digital channels with filters
ca_digital_generator = DigitalChannelGeneratorFromBrandmeister(
    "High",
    usa_tgs,
    aprs_config=digital_aprs_config,
    callsign_matcher=CACallsignMatcher(),
    default_contact_id=parrot_id,
    filter_chain=filter_chain,  # Pass filter chain here
    debug=True
)

channels = ca_digital_generator.channels(sequence)
```

### 4. Sequence ID Assignment

**Before refactoring:**
- All channels were generated and assigned IDs
- Filters were applied after ID assignment
- Filtered-out channels left gaps in the sequence

**After refactoring:**
- Channels are created without IDs initially
- Filters are applied before ID assignment
- Only channels that pass filters receive sequential IDs
- No gaps in the sequence

## Usage Examples

### Example 1: Single Filter

```python
from filters import FilterChain, DistanceFilter

# Create filter chain with single filter
filter_chain = FilterChain([
    DistanceFilter(
        reference_lat=40.7128,
        reference_lng=-74.0060,
        max_distance_km=100.0
    )
])

# Pass to generator
generator = DigitalChannelGeneratorFromBrandmeister(
    power="High",
    talkgroups=usa_tgs,
    aprs_config=aprs_config,
    filter_chain=filter_chain
)

channels = generator.channels(sequence)
```

### Example 2: Multiple Filters

```python
from filters import FilterChain, DistanceFilter, BandFilter

# Combine multiple filters - all must pass
filter_chain = FilterChain([
    DistanceFilter(
        reference_lat=37.4852,
        reference_lng=-122.2364,
        max_distance_km=50.0
    ),
    BandFilter(frequency_ranges=[(144.0, 148.0)])  # 2m only
])

generator = AnalogChannelGeneratorFromRepeaterBook(
    repeaters,
    power="High",
    aprs=aprs_config,
    filter_chain=filter_chain,
    debug=True
)

channels = generator.channels(sequence)
```

### Example 3: Zone Generation with Filters

```python
from filters import FilterChain, DistanceFilter

# Filter channels before creating zones
filter_chain = FilterChain([
    DistanceFilter(
        reference_lat=37.4852,
        reference_lng=-122.2364,
        max_distance_km=50.0
    )
])

zone_generator = ZoneFromCallsignGenerator2(
    channels=all_channels,
    filter_chain=filter_chain,
    debug=True
)

zones = zone_generator.zones(sequence)
```

## Benefits

1. **Sequential IDs**: Only filtered channels receive IDs, maintaining sequence integrity
2. **Efficient**: Filtering happens before ID assignment, avoiding wasted sequence numbers
3. **Composable**: Multiple filters can be easily combined in a chain
4. **Cleaner Code**: Filters are passed as parameters rather than nested wrappers
5. **Easier Testing**: Filters can be tested independently of generators

## Migration Guide

### Old Approach (Wrapper Style)

```python
# OLD: Wrapping generators with filters
ca_digital_generator = DigitalChannelGeneratorFromBrandmeister(...)

# Wrap with distance filter
ca_digital_filtered = DistanceFilter(
    ca_digital_generator,
    reference_lat=37.4852,
    reference_lng=-122.2364,
    max_distance_km=50.0,
    debug=True
)

# Wrap with band filter
ca_digital_filtered = BandFilter(
    ca_digital_filtered,
    debug=True
)

channels = ca_digital_filtered.channels(sequence)
```

### New Approach (Filter Chain)

```python
# NEW: Pass filter chain to generator
filter_chain = FilterChain([
    DistanceFilter(
        reference_lat=37.4852,
        reference_lng=-122.2364,
        max_distance_km=50.0
    ),
    BandFilter()
])

ca_digital_generator = DigitalChannelGeneratorFromBrandmeister(
    ...,
    filter_chain=filter_chain,
    debug=True
)

channels = ca_digital_generator.channels(sequence)
```

## Supported Generators

The following generators now support filter chains:

### Channel Generators
- `DigitalChannelGeneratorFromBrandmeister`
- `AnalogChannelGeneratorFromRepeaterBook`
- `AnalogChannelGeneratorFromPrzemienniki`

### Zone Generators
- `ZoneFromLocatorGenerator`
- `ZoneFromCallsignGenerator`
- `ZoneFromCallsignGenerator2`
- `AnalogZoneByBandGenerator`

## Debug Mode

Enable debug mode to see which items are being filtered out:

```python
filter_chain = FilterChain([
    DistanceFilter(reference_lat=37.0, reference_lng=-122.0, max_distance_km=50.0),
    BandFilter()
])

generator = DigitalChannelGeneratorFromBrandmeister(
    ...,
    filter_chain=filter_chain,
    debug=True  # Enables filter debug output
)
```

Output example:
```
[DigitalChannelGeneratorFromBrandmeister] Filtered out: W6ABC 3100 California - Distance 75.2km exceeds max 50.0km
[DigitalChannelGeneratorFromBrandmeister] Filtered out: K6XYZ TS1 - Frequency 223.5 MHz not in allowed ranges: 144.0-148.0 MHz, 420.0-450.0 MHz
```

## Backward Compatibility

The old wrapper-style filters (`DistanceFilter`, `BandFilter`, `RegionFilter`) have been removed. All code must be migrated to use the new `FilterChain` approach.

## See Also

- `codeplug/filters.py` - Filter implementations
- `codeplug/recipes/usa.py` - Example usage in recipes
- `tests/test_band_filter.py` - Band filter tests
- `tests/test_distance_filter.py` - Distance filter tests
