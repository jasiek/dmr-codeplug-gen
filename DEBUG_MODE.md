# Debug Mode for Filters

## Overview

The debug mode feature allows you to see which records (channels) are being filtered out by the various filters in the codeplug generation process, along with the reason why each record was filtered.

## Usage

Add the `--debug` flag when running the CLI:

```bash
python -m codeplug.cli output.csv CALLSIGN 123456 usa --debug
```

Or with a timezone:

```bash
python -m codeplug.cli output.csv CALLSIGN 123456 usa America/Los_Angeles --debug
```

## What You'll See

When debug mode is enabled, any channel that is filtered out will be printed to stdout with the filter name and reason. For example:

```
[DistanceFilter] Filtered out: W6ABC Repeater - Distance 75.3km exceeds max 50.0km
[BandFilter] Filtered out: K6XYZ Repeater - Frequency 433.0 MHz not in allowed ranges: 144.0-148.0 MHz
[RegionFilter] Filtered out: N6DEF Repeater - Coordinates (39.0000, -121.0000) outside region bounds
```

## Filter Types

### DistanceFilter
Shows channels filtered by distance from a reference point. Reasons include:
- Distance exceeds maximum (e.g., "Distance 75.3km exceeds max 50.0km")
- Missing coordinate attributes
- Coordinates are None
- Coordinate conversion errors

### BandFilter
Shows channels filtered by frequency band. Reasons include:
- Frequency outside allowed ranges (e.g., "Frequency 433.0 MHz not in allowed ranges: 144.0-148.0 MHz")
- Missing rx_freq attribute

### RegionFilter
Shows channels filtered by geographic region bounds. Reasons include:
- Coordinates outside region bounds (e.g., "Coordinates (39.0000, -121.0000) outside region bounds")
- Missing coordinate attributes
- Coordinates are None
- Coordinate conversion errors

## Implementation Details

The debug flag is:
1. Passed from CLI to the Recipe class constructor
2. Stored in the BaseRecipe class
3. Passed to filter constructors (DistanceFilter, BandFilter, RegionFilter)
4. Used by filters to print debug information when filtering records

All filters return tuples of (should_include: bool, reason: str) internally to support debug messaging.
