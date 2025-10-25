# BandFilter Migration Guide

## Overview

The 2m/70cm band filtering logic has been extracted from `AnalogChannelGeneratorFromRepeaterBook` and `AnalogZoneGenerator` into a new, reusable `BandFilter` class in `codeplug/filters.py`.

## What Changed

### 1. New `BandFilter` Class

A new filter class has been added to `codeplug/filters.py`:

```python
from filters import BandFilter

# Default: filters for 2m (144-148 MHz) and 70cm (420-450 MHz)
filtered_gen = BandFilter(generator=my_channel_generator)

# Custom frequency ranges
filtered_gen = BandFilter(
    generator=my_channel_generator,
    frequency_ranges=[(144.0, 148.0), (420.0, 450.0)]
)

channels = filtered_gen.channels(sequence)
```

### 2. Removed Hardcoded Band Filtering

**From `AnalogChannelGeneratorFromRepeaterBook`:**
- Removed the hardcoded check for 2m/70cm bands (lines 156-160)
- Now generates channels for ALL frequency bands
- Use `BandFilter` to filter by band after generation

**From `AnalogZoneGenerator`:**
- Removed the automatic splitting of channels into 2m and 70cm zones
- Now creates a single zone with all provided channels
- Use `BandFilter` to pre-filter channels before passing to zone generator
- Added optional `zone_name` parameter (defaults to "Analog")

## Migration Examples

### Before (Old Pattern)

```python
# Zones were automatically split by band
self.zones = ZoneAggregator(
    AnalogZoneGenerator(self.analog_channels),  # Created "Analog 2m" and "Analog 70cm" zones
).zones(zone_seq)
```

### After (New Pattern)

```python
from filters import BandFilter

# Create filtered channels for each band
band_2m_filter = BandFilter(
    analog_channel_generator,
    frequency_ranges=[(144.0, 148.0)]
)
analog_2m_channels = band_2m_filter.channels(chan_seq)

band_70cm_filter = BandFilter(
    analog_channel_generator,
    frequency_ranges=[(420.0, 450.0)]
)
analog_70cm_channels = band_70cm_filter.channels(chan_seq)

# Create separate zones
self.zones = ZoneAggregator(
    AnalogZoneGenerator(analog_2m_channels, zone_name="Analog 2m"),
    AnalogZoneGenerator(analog_70cm_channels, zone_name="Analog 70cm"),
).zones(zone_seq)
```

## Benefits

1. **Separation of Concerns**: Band filtering is now separate from channel generation and zone creation
2. **Flexibility**: Can easily filter by any frequency range, not just 2m/70cm
3. **Reusability**: The `BandFilter` can be used with any channel generator
4. **Composability**: Can chain multiple filters together
5. **Maintainability**: Changes to band definitions only need to be made in one place

## Usage Examples

### Filter for 2m Only

```python
from filters import BandFilter

# Only 2m band
vhf_filter = BandFilter(
    generator=my_channel_generator,
    frequency_ranges=[(144.0, 148.0)]
)
vhf_channels = vhf_filter.channels(sequence)
```

### Filter for Multiple Bands

```python
from filters import BandFilter

# 2m, 70cm, and 1.25m bands
multi_band_filter = BandFilter(
    generator=my_channel_generator,
    frequency_ranges=[
        (144.0, 148.0),   # 2m
        (222.0, 225.0),   # 1.25m
        (420.0, 450.0),   # 70cm
    ]
)
channels = multi_band_filter.channels(sequence)
```

### Default Behavior

```python
from filters import BandFilter

# Defaults to 2m (144-148 MHz) and 70cm (420-450 MHz)
default_filter = BandFilter(generator=my_channel_generator)
channels = default_filter.channels(sequence)
```

## Files Modified

1. **codeplug/filters.py** - Added `BandFilter` class
2. **codeplug/generators/analogchan.py** - Removed hardcoded 2m/70cm filtering from `AnalogChannelGeneratorFromRepeaterBook`
3. **codeplug/generators/zones.py** - Simplified `AnalogZoneGenerator` to work with pre-filtered channels
4. **codeplug/recipes/usa.py** - Updated to use new `BandFilter` pattern

## Backward Compatibility

**Breaking Change**: The `AnalogZoneGenerator` no longer automatically creates separate zones for 2m and 70cm bands.

**Migration Required**: Update your recipes to use the new `BandFilter` pattern as shown in the examples above.
