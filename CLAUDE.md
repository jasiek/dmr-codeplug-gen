# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based DMR radio codeplug generator that creates configuration files for AnyTone AT-D878UV and other radios supported by [qdmr](https://github.com/hmatuschek/qdmr). It aggregates data from multiple amateur radio data sources (Brandmeister, RepeaterBook, Przemienniki.net) to generate comprehensive codeplugs with channels, zones, contacts, and APRS configurations.

## Build and Development Commands

### Setup
```bash
poetry install
poetry shell
```

### Building Codeplugs
```bash
# Default recipe (Poland)
CALLSIGN=YOUR_CALLSIGN DMRID=YOUR_DMRID make

# USA recipe
CALLSIGN=YOUR_CALLSIGN DMRID=YOUR_DMRID RECIPE=usa make

# Validate the generated codeplug
make validate

# Program the radio (requires qdmr and radio connected)
make program
```

### Testing
```bash
# Run all tests with pytest
pytest

# Run specific test file
pytest tests/test_distance_filter.py
```

### Code Quality
```bash
# Format code with Black (runs automatically during make)
black .

# Lint code
make lint
```

### Cleaning
```bash
# Remove generated codeplug
make clean

# Remove data files and cache
make distclean
```

## Architecture

### Core Concepts

**Recipe Pattern**: The codebase uses a recipe pattern where each geographic region has a dedicated recipe class (e.g., `recipes/poland.py`, `recipes/usa.py`). Recipes orchestrate the entire codeplug generation process by:
- Selecting appropriate data sources
- Configuring generators with region-specific talkgroups and filters
- Assembling contacts, channels, zones, roaming zones, and APRS configurations

**Generator Pattern**: All content generation follows a consistent pattern with `channels(sequence)`, `contacts(sequence)`, `zones(sequence)` methods that accept a `Sequence` object for ID generation. Generators are composable and can be wrapped with filters.

**Aggregator Pattern**: Aggregators (in `codeplug/aggregators.py`) combine multiple generators of the same type (e.g., `ChannelAggregator` combines multiple channel generators) to build comprehensive lists.

**Data Source Caching**: All external API calls are cached using `FileCache` (in `codeplug/datasources/cache.py`) to avoid repeated network requests. Cache files are stored in `cache/` directory organized by data source prefix.

### Key Components

**Models** (`codeplug/models.py`): Type-safe dataclasses defining all radio programming entities:
- `Contact`, `GroupList` for DMR contacts and talkgroups
- `DigitalChannel`, `AnalogChannel` for repeater channels
- `Zone` for organizing channels
- `DigitalRoamingChannel`, `DigitalRoamingZone` for roaming configurations
- All channel types include `_lat`, `_lng`, `_locator`, `_rpt_callsign`, `_qth` metadata for filtering

**Data Sources** (`codeplug/datasources/`):
- `brandmeister.py`: Brandmeister API for DMR repeaters and talkgroups
- `repeaterbook.py`: RepeaterBook API for North American repeaters (includes Nominatim geocoding for missing coordinates)
- `przemienniki.py`: Polish repeater database (XML-based)
- `cache.py`: Generic file-based caching system

**Generators** (`codeplug/generators/`):
- `contacts.py`: Generate DMR contacts from Brandmeister talkgroups
- `digitalchan.py`, `analogchan.py`: Generate channels from various data sources
- `zones.py`: Organize channels into zones by callsign or region
- `roaming.py`: Generate roaming channel configurations
- `grouplists.py`: Create talkgroup lists
- `aprs.py`: Configure APRS positioning systems

**Filters** (`codeplug/filters.py`):
- `DistanceFilter`: Filter channels by distance from a reference point using haversine formula
- `RegionFilter`: Filter channels by geographic bounding box
- Both filters wrap any generator and provide `channels(sequence)` interface

**Callsign Matchers** (`codeplug/callsign_matchers.py`): Filter repeaters by callsign patterns:
- `RegexMatcher`: Match callsigns with regex patterns
- `NYNJCallsignMatcher`: Specialized matcher for NY/NJ call district 2
- `PrefixMatcher`, `MultiMatcher`, `AllMatcher` for various matching strategies

**Radio Implementations** (`codeplug/anytone.py`): Radio-specific codeplug structures (currently supports AT878UV). The radio class coordinates with writers to output the final configuration.

**Writers** (`codeplug/writers.py`): Output format implementations:
- `QDMRWriter`: Writes YAML format compatible with qdmr tool
- Uses `blank_radio/uv878_base.yml` as base template

### Data Flow

1. CLI (`codeplug/cli.py`) receives parameters: output file, callsign, DMR ID, recipe name
2. Recipe's `prepare()` method:
   - Creates `Sequence` objects for generating unique internal IDs
   - Instantiates data sources (cached API wrappers)
   - Configures generators with region-specific filters and matchers
   - Uses aggregators to combine multiple generators
   - Stores results in recipe instance variables
3. Recipe's `generate()` method:
   - Instantiates radio class with all prepared data
   - Calls radio's `generate(writer)` which coordinates writing all sections
4. Writer outputs final YAML codeplug file

### Adding New Regions

To add a new region recipe:
1. Create `codeplug/recipes/<region>.py` inheriting from `BaseRecipe`
2. Implement `prepare()` method to configure generators with region-specific:
   - Talkgroups (use `brandmeister_contact_gen.matched_contacts("^COUNTRY_CODE")`)
   - Data sources (RepeaterBook state codes, or other APIs)
   - Callsign matchers for filtering repeaters
   - Optional distance/region filters for geographic bounding
3. Assign to `self.contacts`, `self.digital_channels`, `self.analog_channels`, `self.zones`, `self.roaming_channels`, `self.roaming_zones`, `self.grouplists`, `self.analog_aprs_config`, `self.digital_aprs_config`
4. Update `Makefile` to support new recipe name

### Testing

Tests use pytest and follow the pattern `tests/test_*.py`. The `pyproject.toml` configures pytest with:
- Python path includes project root
- Test discovery in `tests/` directory
- Automatically discovers `test_*.py` files

Current test coverage focuses on filters (distance calculations). When adding new filters or generators, add corresponding tests following the existing patterns.
