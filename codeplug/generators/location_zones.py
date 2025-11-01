import math
from collections import defaultdict
from typing import List, Optional, Tuple

from models import Zone, DigitalChannel, AnalogChannel


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
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


class LocationClusterZoneGenerator:
    """
    Zone generator that clusters repeaters by geographical location using distance-based clustering.

    This generator groups repeaters that are within a specified distance threshold into the same zone,
    creating geographical clusters. Each cluster is named based on a representative location or callsign.
    """

    def __init__(
        self,
        channels: List,
        max_distance_km: float = 25.0,
        min_repeaters_per_zone: int = 2,
        zone_naming: str = "representative",  # "representative", "centroid", "center"
        include_qth_in_name: bool = True,
    ):
        """
        Initialize the location cluster zone generator.

        Args:
            channels: List of channels to cluster
            max_distance_km: Maximum distance in kilometers between repeaters in same cluster
            min_repeaters_per_zone: Minimum number of repeaters required to form a zone
            zone_naming: How to name zones - "representative", "centroid", or "center"
            include_qth_in_name: Whether to include QTH information in zone names
        """
        self.channels = channels
        self.max_distance_km = max_distance_km
        self.min_repeaters_per_zone = min_repeaters_per_zone
        self.zone_naming = zone_naming
        self.include_qth_in_name = include_qth_in_name

    def _get_location(self, channel) -> Optional[Tuple[float, float]]:
        """Extract latitude and longitude from channel, return None if not available."""
        if hasattr(channel, "_lat") and hasattr(channel, "_lng"):
            if channel._lat is not None and channel._lng is not None:
                return (channel._lat, channel._lng)
        return None

    def _calculate_centroid(
        self, locations: List[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """Calculate the centroid of a list of lat/lon pairs."""
        if not locations:
            return (0.0, 0.0)

        avg_lat = sum(loc[0] for loc in locations) / len(locations)
        avg_lon = sum(loc[1] for loc in locations) / len(locations)
        return (avg_lat, avg_lon)

    def _find_closest_repeater(
        self, target_location: Tuple[float, float], used_repeaters: set
    ) -> Optional[Tuple]:
        """Find the closest unused repeater to the target location."""
        min_distance = float("inf")
        closest_repeater = None

        for channel in self.channels:
            if id(channel) in used_repeaters:
                continue

            location = self._get_location(channel)
            if location is None:
                continue

            distance = haversine_distance(
                target_location[0], target_location[1], location[0], location[1]
            )
            if distance < min_distance:
                min_distance = distance
                closest_repeater = channel

        return closest_repeater if min_distance <= self.max_distance_km else None

    def _cluster_repeaters(self) -> List[List]:
        """Cluster repeaters using a greedy distance-based algorithm."""
        used_repeaters = set()
        clusters = []

        # Start with each unclustered repeater as a potential cluster center
        for start_channel in self.channels:
            if id(start_channel) in used_repeaters:
                continue

            location = self._get_location(start_channel)
            if location is None:
                continue

            cluster = [start_channel]
            used_repeaters.add(id(start_channel))

            # Find all repeaters within max_distance_km of this cluster
            while True:
                closest = self._find_closest_repeater(location, used_repeaters)
                if closest is None:
                    break

                cluster.append(closest)
                used_repeaters.add(id(closest))

                # Update cluster center to centroid of all repeaters in cluster
                cluster_locations = [
                    self._get_location(c)
                    for c in cluster
                    if self._get_location(c) is not None
                ]
                if cluster_locations:
                    location = self._calculate_centroid(cluster_locations)

            # Only add clusters with sufficient repeaters
            if len(cluster) >= self.min_repeaters_per_zone:
                clusters.append(cluster)

        return clusters

    def _generate_zone_name(self, cluster: List) -> str:
        """Generate a zone name based on the cluster and naming strategy."""
        cluster_locations = [
            self._get_location(c) for c in cluster if self._get_location(c) is not None
        ]

        if self.zone_naming == "representative":
            # Use the most central repeater (or first one) as representative
            representative = cluster[0]
            if (
                hasattr(representative, "_rpt_callsign")
                and representative._rpt_callsign
            ):
                name = representative._rpt_callsign
                if (
                    self.include_qth_in_name
                    and hasattr(representative, "_qth")
                    and representative._qth
                ):
                    name += f" {representative._qth}"
            else:
                name = f"Cluster {len(clusters) + 1}"

        elif self.zone_naming == "centroid":
            # Use centroid location for naming
            centroid = self._calculate_centroid(cluster_locations)
            name = f"Zone {centroid[0]:.2f}°N {centroid[1]:.2f}°W"

        elif self.zone_naming == "center":
            # Find the repeater closest to the center
            centroid = self._calculate_centroid(cluster_locations)
            center_repeater = min(
                cluster,
                key=lambda c: haversine_distance(
                    centroid[0], centroid[1], *self._get_location(c) or (0, 0)
                ),
            )

            if (
                hasattr(center_repeater, "_rpt_callsign")
                and center_repeater._rpt_callsign
            ):
                name = center_repeater._rpt_callsign
                if (
                    self.include_qth_in_name
                    and hasattr(center_repeater, "_qth")
                    and center_repeater._qth
                ):
                    name += f" {center_repeater._qth}"
            else:
                name = f"Center Zone {len(clusters) + 1}"
        else:
            name = f"Cluster {len(clusters) + 1}"

        # Add cluster size for context
        name += f" ({len(cluster)} repeaters)"

        return name

    def zones(self, sequence):
        """Generate zones based on geographical clustering."""
        # Filter channels with valid location data
        channels_with_location = [
            c for c in self.channels if self._get_location(c) is not None
        ]

        if len(channels_with_location) < self.min_repeaters_per_zone:
            print(
                f"Not enough repeaters with location data ({len(channels_with_location)}) "
                f"to form zones (minimum: {self.min_repeaters_per_zone})"
            )
            return []

        clusters = self._cluster_repeaters()
        zones = []

        for cluster in clusters:
            channel_ids = [chan.internal_id for chan in cluster]
            zone_name = self._generate_zone_name(cluster)
            zones.append(
                Zone(internal_id=sequence.next(), name=zone_name, channels=channel_ids)
            )

        # Sort zones by name for consistent output
        zones.sort(key=lambda z: z.name)

        print(
            f"Created {len(zones)} location-based zones from {len(channels_with_location)} repeaters"
        )
        print(
            f"Zone parameters: max_distance={self.max_distance_km}km, min_repeaters={self.min_repeaters_per_zone}"
        )

        return zones


class DistanceBandedZoneGenerator:
    """
    Zone generator that creates zones based on distance bands from a reference point.

    This creates zones like "Local (0-25km)", "Regional (25-100km)", etc.
    """

    def __init__(
        self,
        channels: List,
        reference_lat: float,
        reference_lon: float,
        distance_bands: List[Tuple[str, float, float]],  # [(name, min_km, max_km), ...]
        include_qth_in_name: bool = True,
    ):
        """
        Initialize the distance banded zone generator.

        Args:
            channels: List of channels to zone
            reference_lat: Reference latitude for distance calculations
            reference_lon: Reference longitude for distance calculations
            distance_bands: List of (name, min_km, max_km) tuples defining distance bands
            include_qth_in_name: Whether to include QTH information in zone names
        """
        self.channels = channels
        self.reference_lat = reference_lat
        self.reference_lon = reference_lon
        self.distance_bands = distance_bands
        self.include_qth_in_name = include_qth_in_name

    def _get_distance_from_reference(self, channel) -> Optional[float]:
        """Calculate distance from reference point, return None if no location data."""
        if hasattr(channel, "_lat") and hasattr(channel, "_lng"):
            if channel._lat is not None and channel._lng is not None:
                return haversine_distance(
                    self.reference_lat, self.reference_lon, channel._lat, channel._lng
                )
        return None

    def zones(self, sequence):
        """Generate zones based on distance bands from reference point."""
        bands_to_channels = defaultdict(lambda: [])

        # Sort channels into distance bands
        for channel in self.channels:
            distance = self._get_distance_from_reference(channel)
            if distance is None:
                continue

            assigned = False
            for band_name, min_km, max_km in self.distance_bands:
                if min_km <= distance < max_km:
                    bands_to_channels[band_name].append(channel)
                    assigned = True
                    break

            # Optionally handle channels outside all bands
            if not assigned:
                for band_name, min_km, max_km in self.distance_bands:
                    if min_km == 0 and distance >= max_km:
                        bands_to_channels[f"{band_name}+"].append(channel)
                        assigned = True
                        break

        zones = []
        for band_name in sorted(bands_to_channels.keys()):
            channels = sorted(bands_to_channels[band_name], key=lambda chan: chan.name)
            channel_ids = [chan.internal_id for chan in channels]

            if len(channel_ids) > 0:
                zone_name = f"{band_name} ({len(channel_ids)} repeaters)"
                zones.append(
                    Zone(
                        internal_id=sequence.next(),
                        name=zone_name,
                        channels=channel_ids,
                    )
                )

        print(
            f"Created {len(zones)} distance-banded zones from {len(self.channels)} repeaters"
        )

        return zones
