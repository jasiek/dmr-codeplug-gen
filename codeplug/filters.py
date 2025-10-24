import math
from typing import Optional, Union


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


class DistanceFilter:
    """
    A filter that wraps any channel generator and filters channels by distance from a reference point.

    Usage:
        # Filter channels to only include those within 50km of New York City
        filtered_gen = DistanceFilter(
            generator=my_channel_generator,
            reference_lat=40.7128,
            reference_lng=-74.0060,
            max_distance_km=50.0
        )
        channels = filtered_gen.channels(sequence)
    """

    def __init__(
        self,
        generator,
        reference_lat: float,
        reference_lng: float,
        max_distance_km: float,
        include_channels_without_coordinates: bool = False,
    ):
        """
        Initialize the distance filter.

        Args:
            generator: Any object with a channels(sequence) method that returns channels
            reference_lat: Reference latitude in decimal degrees
            reference_lng: Reference longitude in decimal degrees
            max_distance_km: Maximum distance in kilometers from reference point
            include_channels_without_coordinates: Whether to include channels that don't have lat/lng
        """
        self.generator = generator
        self.reference_lat = reference_lat
        self.reference_lng = reference_lng
        self.max_distance_km = max_distance_km
        self.include_channels_without_coordinates = include_channels_without_coordinates
        self._filtered_channels = None

    def channels(self, sequence):
        """
        Generate filtered channels based on distance criteria.

        Args:
            sequence: Sequence object for generating internal IDs

        Returns:
            List of channels within the specified distance
        """
        if self._filtered_channels is None:
            self._filtered_channels = self._filter_channels(sequence)
        return self._filtered_channels

    def _filter_channels(self, sequence):
        """
        Internal method to perform the actual filtering.
        """
        all_channels = self.generator.channels(sequence)
        filtered_channels = []

        for channel in all_channels:
            if self._should_include_channel(channel):
                filtered_channels.append(channel)

        return filtered_channels

    def _should_include_channel(self, channel) -> bool:
        """
        Determine if a channel should be included based on distance criteria.

        Args:
            channel: Channel object to evaluate

        Returns:
            True if channel should be included, False otherwise
        """
        # Check if channel has coordinates
        if not hasattr(channel, "_lat") or not hasattr(channel, "_lng"):
            return self.include_channels_without_coordinates

        lat = channel._lat
        lng = channel._lng

        # Handle channels without coordinates
        if lat is None or lng is None:
            return self.include_channels_without_coordinates

        # Calculate distance and check if within range
        try:
            distance = haversine_distance(
                self.reference_lat, self.reference_lng, float(lat), float(lng)
            )
            return distance <= self.max_distance_km
        except (ValueError, TypeError):
            # If coordinate conversion fails, apply fallback policy
            return self.include_channels_without_coordinates


class RegionFilter:
    """
    A filter that wraps any channel generator and filters channels by geographic region bounds.

    Usage:
        # Filter channels to only include those within a bounding box
        filtered_gen = RegionFilter(
            generator=my_channel_generator,
            min_lat=40.0,
            max_lat=41.0,
            min_lng=-75.0,
            max_lng=-73.0
        )
        channels = filtered_gen.channels(sequence)
    """

    def __init__(
        self,
        generator,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        include_channels_without_coordinates: bool = False,
    ):
        """
        Initialize the region filter.

        Args:
            generator: Any object with a channels(sequence) method that returns channels
            min_lat: Minimum latitude bound
            max_lat: Maximum latitude bound
            min_lng: Minimum longitude bound
            max_lng: Maximum longitude bound
            include_channels_without_coordinates: Whether to include channels that don't have lat/lng
        """
        self.generator = generator
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lng = min_lng
        self.max_lng = max_lng
        self.include_channels_without_coordinates = include_channels_without_coordinates
        self._filtered_channels = None

    def channels(self, sequence):
        """
        Generate filtered channels based on region criteria.

        Args:
            sequence: Sequence object for generating internal IDs

        Returns:
            List of channels within the specified region
        """
        if self._filtered_channels is None:
            self._filtered_channels = self._filter_channels(sequence)
        return self._filtered_channels

    def _filter_channels(self, sequence):
        """
        Internal method to perform the actual filtering.
        """
        all_channels = self.generator.channels(sequence)
        filtered_channels = []

        for channel in all_channels:
            if self._should_include_channel(channel):
                filtered_channels.append(channel)

        return filtered_channels

    def _should_include_channel(self, channel) -> bool:
        """
        Determine if a channel should be included based on region criteria.

        Args:
            channel: Channel object to evaluate

        Returns:
            True if channel should be included, False otherwise
        """
        # Check if channel has coordinates
        if not hasattr(channel, "_lat") or not hasattr(channel, "_lng"):
            return self.include_channels_without_coordinates

        lat = channel._lat
        lng = channel._lng

        # Handle channels without coordinates
        if lat is None or lng is None:
            return self.include_channels_without_coordinates

        # Check if coordinates are within bounds
        try:
            lat_float = float(lat)
            lng_float = float(lng)

            return (
                self.min_lat <= lat_float <= self.max_lat
                and self.min_lng <= lng_float <= self.max_lng
            )
        except (ValueError, TypeError):
            # If coordinate conversion fails, apply fallback policy
            return self.include_channels_without_coordinates
