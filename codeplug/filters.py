import math
from typing import Optional, Union, List, Tuple, Callable, Any


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


class FilterChain:
    """
    A chain of filters that can be passed to channel/zone generators.
    Each filter in the chain is applied in sequence, and a channel must pass all filters.
    """

    def __init__(self, filters: List["BaseFilter"] = None):
        """
        Initialize the filter chain.

        Args:
            filters: List of BaseFilter instances to apply
        """
        self.filters = filters or []

    def add_filter(self, filter_instance: "BaseFilter") -> "FilterChain":
        """
        Add a filter to the chain.

        Args:
            filter_instance: A BaseFilter instance to add

        Returns:
            Self for method chaining
        """
        self.filters.append(filter_instance)
        return self

    def should_include(self, item: Any) -> Tuple[bool, str]:
        """
        Test if an item should be included based on all filters in the chain.

        Args:
            item: The item (channel, zone, etc.) to test

        Returns:
            Tuple of (should_include, reason) where should_include is bool and reason is string
        """
        for filter_instance in self.filters:
            should_include, reason = filter_instance.should_include(item)
            if not should_include:
                return (False, reason)
        return (True, "")

    def filter_items(self, items: List[Any], debug: bool = False) -> List[Any]:
        """
        Filter a list of items using the filter chain.

        Args:
            items: List of items to filter
            debug: If True, print debug information for filtered items

        Returns:
            Filtered list of items
        """
        filtered_items = []
        for item in items:
            should_include, reason = self.should_include(item)
            if should_include:
                filtered_items.append(item)
            elif debug:
                item_name = getattr(item, "name", str(item))
                print(f"[FilterChain] Filtered out: {item_name} - {reason}")
        return filtered_items

    def __len__(self) -> int:
        """Return the number of filters in the chain."""
        return len(self.filters)

    def __bool__(self) -> bool:
        """Return True if there are filters in the chain."""
        return len(self.filters) > 0


class BaseFilter:
    """
    Base class for all filters. Filters test whether an item should be included.
    """

    def should_include(self, item: Any) -> Tuple[bool, str]:
        """
        Determine if an item should be included.

        Args:
            item: The item to test

        Returns:
            Tuple of (should_include, reason) where should_include is bool and reason is string
        """
        raise NotImplementedError("Subclasses must implement should_include")


class DistanceFilter(BaseFilter):
    """
    A filter that tests channels by distance from a reference point.

    Usage:
        filter_chain = FilterChain([
            DistanceFilter(
                reference_lat=40.7128,
                reference_lng=-74.0060,
                max_distance_km=50.0
            )
        ])
        generator = MyChannelGenerator(filter_chain=filter_chain)
        channels = generator.channels(sequence)
    """

    def __init__(
        self,
        reference_lat: float,
        reference_lng: float,
        max_distance_km: float,
        include_items_without_coordinates: bool = False,
    ):
        """
        Initialize the distance filter.

        Args:
            reference_lat: Reference latitude in decimal degrees
            reference_lng: Reference longitude in decimal degrees
            max_distance_km: Maximum distance in kilometers from reference point
            include_items_without_coordinates: Whether to include items that don't have lat/lng
        """
        self.reference_lat = reference_lat
        self.reference_lng = reference_lng
        self.max_distance_km = max_distance_km
        self.include_items_without_coordinates = include_items_without_coordinates

    def should_include(self, item: Any) -> Tuple[bool, str]:
        """
        Determine if an item should be included based on distance criteria.

        Args:
            item: Item object to evaluate (typically a channel)

        Returns:
            Tuple of (should_include, reason)
        """
        # Check if item has coordinates
        if not hasattr(item, "_lat") or not hasattr(item, "_lng"):
            if self.include_items_without_coordinates:
                return (True, "")
            else:
                return (False, "Missing coordinate attributes")

        lat = item._lat
        lng = item._lng

        # Handle items without coordinates
        if lat is None or lng is None:
            if self.include_items_without_coordinates:
                return (True, "")
            else:
                return (False, "Coordinates are None")

        # Calculate distance and check if within range
        try:
            distance = haversine_distance(
                self.reference_lat, self.reference_lng, float(lat), float(lng)
            )
            if distance <= self.max_distance_km:
                return (True, "")
            else:
                return (
                    False,
                    f"Distance {distance:.1f}km exceeds max {self.max_distance_km}km",
                )
        except (ValueError, TypeError) as e:
            # If coordinate conversion fails, apply fallback policy
            if self.include_items_without_coordinates:
                return (True, "")
            else:
                return (False, f"Coordinate conversion error: {e}")


class RegionFilter(BaseFilter):
    """
    A filter that tests channels by geographic region bounds.

    Usage:
        filter_chain = FilterChain([
            RegionFilter(
                min_lat=40.0,
                max_lat=41.0,
                min_lng=-75.0,
                max_lng=-73.0
            )
        ])
        generator = MyChannelGenerator(filter_chain=filter_chain)
        channels = generator.channels(sequence)
    """

    def __init__(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        include_items_without_coordinates: bool = False,
    ):
        """
        Initialize the region filter.

        Args:
            min_lat: Minimum latitude bound
            max_lat: Maximum latitude bound
            min_lng: Minimum longitude bound
            max_lng: Maximum longitude bound
            include_items_without_coordinates: Whether to include items that don't have lat/lng
        """
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lng = min_lng
        self.max_lng = max_lng
        self.include_items_without_coordinates = include_items_without_coordinates

    def should_include(self, item: Any) -> Tuple[bool, str]:
        """
        Determine if an item should be included based on region criteria.

        Args:
            item: Item object to evaluate

        Returns:
            Tuple of (should_include, reason)
        """
        # Check if item has coordinates
        if not hasattr(item, "_lat") or not hasattr(item, "_lng"):
            if self.include_items_without_coordinates:
                return (True, "")
            else:
                return (False, "Missing coordinate attributes")

        lat = item._lat
        lng = item._lng

        # Handle items without coordinates
        if lat is None or lng is None:
            if self.include_items_without_coordinates:
                return (True, "")
            else:
                return (False, "Coordinates are None")

        # Check if coordinates are within bounds
        try:
            lat_float = float(lat)
            lng_float = float(lng)

            if (
                self.min_lat <= lat_float <= self.max_lat
                and self.min_lng <= lng_float <= self.max_lng
            ):
                return (True, "")
            else:
                return (
                    False,
                    f"Coordinates ({lat_float:.4f}, {lng_float:.4f}) outside region bounds",
                )
        except (ValueError, TypeError) as e:
            # If coordinate conversion fails, apply fallback policy
            if self.include_items_without_coordinates:
                return (True, "")
            else:
                return (False, f"Coordinate conversion error: {e}")


class BandFilter(BaseFilter):
    """
    A filter that tests channels by frequency band.
    By default, only passes through channels in the 2m (144-148 MHz) and 70cm (420-450 MHz) bands.

    Usage:
        filter_chain = FilterChain([
            BandFilter()  # Uses default 2m and 70cm bands
        ])
        generator = MyChannelGenerator(filter_chain=filter_chain)
        channels = generator.channels(sequence)

        # Or specify custom frequency ranges
        filter_chain = FilterChain([
            BandFilter(frequency_ranges=[(144.0, 148.0), (420.0, 450.0)])
        ])
    """

    def __init__(
        self,
        frequency_ranges: list[tuple[float, float]] = None,
    ):
        """
        Initialize the band filter.

        Args:
            frequency_ranges: List of (min_freq, max_freq) tuples in MHz.
                            Defaults to [(144.0, 148.0), (420.0, 450.0)] for 2m and 70cm bands.
        """
        if frequency_ranges is None:
            # Default to 2m and 70cm bands
            self.frequency_ranges = [(144.0, 148.0), (420.0, 450.0)]
        else:
            self.frequency_ranges = frequency_ranges

    def should_include(self, item: Any) -> Tuple[bool, str]:
        """
        Determine if an item should be included based on frequency band criteria.

        Args:
            item: Item object to evaluate (typically a channel)

        Returns:
            Tuple of (should_include, reason)
        """
        # Check if item has rx_freq attribute
        if not hasattr(item, "rx_freq"):
            return (False, "Missing rx_freq attribute")

        rx_freq = item.rx_freq

        # Check if frequency falls within any of the allowed ranges
        for min_freq, max_freq in self.frequency_ranges:
            if min_freq <= rx_freq <= max_freq:
                return (True, "")

        # Build a reason string showing the allowed ranges
        ranges_str = ", ".join(
            [f"{min_f}-{max_f} MHz" for min_f, max_f in self.frequency_ranges]
        )
        return (False, f"Frequency {rx_freq} MHz not in allowed ranges: {ranges_str}")


def sort_channels_by_distance(
    channels: List,
    reference_lat: float,
    reference_lng: float,
    channels_without_coordinates_last: bool = True,
) -> List:
    """
    Sort a list of channels by distance from a reference point.

    Args:
        channels: List of channel objects to sort
        reference_lat: Reference latitude in decimal degrees
        reference_lng: Reference longitude in decimal degrees
        channels_without_coordinates_last: If True, channels without coordinates
                                          are placed at the end. If False, they're
                                          placed at the beginning.

    Returns:
        Sorted list of channels
    """

    def get_channel_distance(channel) -> Tuple[bool, float]:
        """
        Calculate distance for a channel, returning a tuple for sorting.
        First element is whether coordinates exist, second is distance.
        """
        # Check if channel has coordinates
        if not hasattr(channel, "_lat") or not hasattr(channel, "_lng"):
            return (False, float("inf"))

        lat = channel._lat
        lng = channel._lng

        # Handle channels without coordinates
        if lat is None or lng is None:
            return (False, float("inf"))

        # Calculate distance
        try:
            distance = haversine_distance(
                reference_lat, reference_lng, float(lat), float(lng)
            )
            return (True, distance)
        except (ValueError, TypeError):
            return (False, float("inf"))

    # Sort channels
    if channels_without_coordinates_last:
        # Channels with coordinates first (sorted by distance), then without
        sorted_channels = sorted(
            channels,
            key=lambda ch: (
                not get_channel_distance(ch)[0],
                get_channel_distance(ch)[1],
            ),
        )
    else:
        # Channels without coordinates first, then with (sorted by distance)
        sorted_channels = sorted(
            channels,
            key=lambda ch: (get_channel_distance(ch)[0], get_channel_distance(ch)[1]),
        )

    return sorted_channels


def sort_zones_by_distance(
    zones: List,
    channels: List,
    reference_lat: float,
    reference_lng: float,
    zones_without_coordinates_last: bool = True,
) -> List:
    """
    Sort a list of zones by the minimum distance of their channels from a reference point.

    The zone's distance is determined by the closest channel within that zone.

    Args:
        zones: List of zone objects to sort
        channels: List of all channel objects (needed to look up zone channels)
        reference_lat: Reference latitude in decimal degrees
        reference_lng: Reference longitude in decimal degrees
        zones_without_coordinates_last: If True, zones with no valid coordinates
                                       are placed at the end.

    Returns:
        Sorted list of zones
    """
    # Create a mapping of channel IDs to channels for quick lookup
    channel_map = {ch.internal_id: ch for ch in channels}

    def get_zone_distance(zone) -> Tuple[bool, float]:
        """
        Calculate the minimum distance for a zone based on its channels.
        Returns tuple of (has_coordinates, min_distance).
        """
        min_distance = float("inf")
        has_valid_channel = False

        # Get all channels in the zone
        for channel_id in zone.channels:
            channel = channel_map.get(channel_id)
            if channel is None:
                continue

            # Check if channel has coordinates
            if not hasattr(channel, "_lat") or not hasattr(channel, "_lng"):
                continue

            lat = channel._lat
            lng = channel._lng

            if lat is None or lng is None:
                continue

            # Calculate distance
            try:
                distance = haversine_distance(
                    reference_lat, reference_lng, float(lat), float(lng)
                )
                min_distance = min(min_distance, distance)
                has_valid_channel = True
            except (ValueError, TypeError):
                continue

        return (has_valid_channel, min_distance)

    # Sort zones
    if zones_without_coordinates_last:
        # Zones with valid channels first (sorted by min distance), then without
        sorted_zones = sorted(
            zones, key=lambda z: (not get_zone_distance(z)[0], get_zone_distance(z)[1])
        )
    else:
        # Zones without valid channels first, then with (sorted by min distance)
        sorted_zones = sorted(
            zones, key=lambda z: (get_zone_distance(z)[0], get_zone_distance(z)[1])
        )

    return sorted_zones
