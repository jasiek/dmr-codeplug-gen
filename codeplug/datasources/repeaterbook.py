import requests
import time
from .cache import FileCache


class NominatimGeocoder(FileCache):
    """
    OSM Nominatim geocoding service with caching
    """

    def __init__(self, user_agent="dmr-codeplug-gen, jan.szumiec@gmail.com"):
        FileCache.__init__(self, "nominatim")
        self.user_agent = user_agent
        self.base_url = "https://nominatim.openstreetmap.org"
        self.last_request_time = 0
        self.min_delay = 1.0  # Nominatim requires 1 second between requests

    def _rate_limit(self):
        """Ensure we respect Nominatim's rate limiting requirements"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        self.last_request_time = time.time()

    def geocode(self, city, state=None, country=None):
        """
        Geocode a city to get coordinates

        Args:
            city: City name
            state: State/province name (optional)
            country: Country name (optional)

        Returns:
            dict with 'lat' and 'lon' keys, or None if not found
        """
        if not city or not city.strip():
            return None

        # Build query string
        query_parts = [city.strip()]
        if state:
            query_parts.append(state.strip())
        if country:
            query_parts.append(country.strip())

        query = ", ".join(query_parts)

        # Create cache key from query
        cache_key = f"geocode_{query.lower().replace(' ', '_').replace(',', '_')}"

        # Check cache first
        import os.path

        cache_filename = (
            f"{self._FileCache__cache_dir()}/{cache_key}.{self.method.__name__}"
        )
        if os.path.isfile(cache_filename):
            content = open(cache_filename).read()
            cached_result = self.method.loads(content)
            if cached_result:  # Only return if we have a valid result
                return cached_result

        # Make request with rate limiting
        self._rate_limit()

        params = {"q": query, "format": "json", "limit": 1, "addressdetails": 1}

        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(
                f"{self.base_url}/search", params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            results = response.json()
            if results and len(results) > 0:
                result = results[0]
                coords = {"lat": float(result["lat"]), "lon": float(result["lon"])}
                # Cache the result
                self.write_cache(cache_key, coords)
                return coords
            else:
                # Cache negative result to avoid repeated requests
                self.write_cache(cache_key, None)
                return None

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Geocoding failed for '{query}': {e}")
            # Cache negative result
            self.write_cache(cache_key, None)
            return None


class RepeaterBookAPI(FileCache):
    """
    RepeaterBook API data source

    Provides access to repeater data from RepeaterBook.com
    Supports both North America and international repeaters
    Enhanced with OSM Nominatim geocoding for missing coordinates
    """

    def __init__(self, user_agent="dmr-codeplug-gen, jan.szumiec@gmail.com"):
        FileCache.__init__(self, "repeaterbook")
        self.user_agent = user_agent
        self.base_url = "https://www.repeaterbook.com/api"
        self.geocoder = NominatimGeocoder(user_agent)

    def _get_headers(self):
        """Get required headers including User-Agent for API authentication"""
        return {"User-Agent": self.user_agent}

    def _build_params(self, **kwargs):
        """Build query parameters, filtering out None values"""
        return {k: v for k, v in kwargs.items() if v is not None}

    def _enhance_with_coordinates(self, data):
        """
        Enhance repeater data with coordinates from Nominatim when missing

        Args:
            data: RepeaterBook API response data

        Returns:
            Enhanced data with geocoded coordinates where missing
        """
        if not isinstance(data, dict) or "results" not in data:
            return data

        enhanced_results = []

        for repeater in data["results"]:
            enhanced_repeater = repeater.copy()

            # Check if coordinates are missing or invalid
            has_coords = (
                repeater.get("Lat")
                and repeater.get("Long")
                and float(repeater.get("Lat", 0)) != 0
                and float(repeater.get("Long", 0)) != 0
            )

            if not has_coords:
                # Try to geocode based on available location information
                city = repeater.get("Nearest City") or repeater.get("Landmark")
                state = repeater.get("State")
                country = repeater.get("Country")

                if city:
                    print(f"Geocoding {city}, {state or ''}, {country or ''}")
                    coords = self.geocoder.geocode(city, state, country)

                    if coords:
                        enhanced_repeater["Lat"] = str(coords["lat"])
                        enhanced_repeater["Long"] = str(coords["lon"])
                        enhanced_repeater["_geocoded"] = True
                        print(
                            f"  -> Found coordinates: {coords['lat']}, {coords['lon']}"
                        )
                    else:
                        print(f"  -> Geocoding failed for {city}")
                        enhanced_repeater["_geocoded"] = False
                else:
                    enhanced_repeater["_geocoded"] = False
            else:
                enhanced_repeater["_geocoded"] = False  # Already had coordinates

            enhanced_results.append(enhanced_repeater)

        # Return enhanced data
        enhanced_data = data.copy()
        enhanced_data["results"] = enhanced_results
        return enhanced_data

    def _make_request(self, endpoint, **params):
        """Make API request with proper headers and caching"""
        # Create cache key from endpoint and sorted params
        cache_key = f"{endpoint}_" + "_".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )

        # Build full URL
        url = f"{self.base_url}/{endpoint}"

        # Check cache first
        import os.path

        cache_filename = (
            f"{self._FileCache__cache_dir()}/{cache_key}.{self.method.__name__}"
        )
        if os.path.isfile(cache_filename):
            content = open(cache_filename).read()
            data = self.method.loads(content)
            # Enhance with coordinates if needed
            return self._enhance_with_coordinates(data)
        else:
            # Make request with headers
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            content = response.json()
            # Enhance with coordinates before caching
            enhanced_content = self._enhance_with_coordinates(content)
            self.write_cache(cache_key, enhanced_content)
            return enhanced_content

    def get_repeaters_by_country(self, country, **filters):
        """
        Get repeaters by country

        Args:
            country: Country name (e.g., "United States", "Canada", "Switzerland")
            **filters: Additional filters like callsign, city, state_id, frequency, mode, etc.
        """
        # Determine endpoint based on country
        if country.lower() in ["united states", "canada"]:
            endpoint = "export.php"
        else:
            endpoint = "exportROW.php"

        params = self._build_params(country=country, **filters)
        return self._make_request(endpoint, **params)

    def get_repeaters_by_state(self, state_id, country="United States", **filters):
        """
        Get repeaters by US state or Canadian province

        Args:
            state_id: State FIPS code (e.g., "06" for California)
            country: Country name (default: "United States")
            **filters: Additional filters like callsign, city, frequency, mode, etc.
        """
        params = self._build_params(state_id=state_id, country=country, **filters)
        return self._make_request("export.php", **params)

    def get_repeaters_by_callsign(self, callsign, country=None, **filters):
        """
        Get repeaters by callsign (supports wildcards with %)

        Args:
            callsign: Callsign to search for (e.g., "W1AW", "KD6%", "%KPC")
            country: Optional country filter
            **filters: Additional filters
        """
        # Determine endpoint based on country
        if country and country.lower() not in ["united states", "canada"]:
            endpoint = "exportROW.php"
        else:
            endpoint = "export.php"

        params = self._build_params(callsign=callsign, country=country, **filters)
        return self._make_request(endpoint, **params)

    def get_repeaters_by_frequency(self, frequency, country=None, **filters):
        """
        Get repeaters by frequency

        Args:
            frequency: Frequency to search for (e.g., "146.52")
            country: Optional country filter
            **filters: Additional filters
        """
        # Determine endpoint based on country
        if country and country.lower() not in ["united states", "canada"]:
            endpoint = "exportROW.php"
        else:
            endpoint = "export.php"

        params = self._build_params(frequency=frequency, country=country, **filters)
        return self._make_request(endpoint, **params)

    def get_repeaters_by_city(self, city, country=None, **filters):
        """
        Get repeaters by city

        Args:
            city: City name to search for
            country: Optional country filter
            **filters: Additional filters
        """
        # Determine endpoint based on country
        if country and country.lower() not in ["united states", "canada"]:
            endpoint = "exportROW.php"
        else:
            endpoint = "export.php"

        params = self._build_params(city=city, country=country, **filters)
        return self._make_request(endpoint, **params)

    def get_digital_repeaters(self, mode, country=None, **filters):
        """
        Get digital repeaters by mode

        Args:
            mode: Digital mode ("DMR", "NXDN", "P25", "tetra", etc.)
            country: Optional country filter
            **filters: Additional filters
        """
        # Determine endpoint based on country
        if country and country.lower() not in ["united states", "canada"]:
            endpoint = "exportROW.php"
        else:
            endpoint = "export.php"

        params = self._build_params(mode=mode, country=country, **filters)
        return self._make_request(endpoint, **params)

    def get_emergency_repeaters(self, emcomm_type, country=None, **filters):
        """
        Get emergency communication repeaters

        Args:
            emcomm_type: Emergency communication type ("ARES", "RACES", "SKYWARN", "CANWARN")
            country: Optional country filter
            **filters: Additional filters
        """
        # Only available for North America endpoint
        endpoint = "export.php"
        params = self._build_params(emcomm=emcomm_type, country=country, **filters)
        return self._make_request(endpoint, **params)

    def get_gmrs_repeaters(self, **filters):
        """
        Get GMRS repeaters (US only)

        Args:
            **filters: Additional filters like city, state_id, frequency, etc.
        """
        params = self._build_params(stype="gmrs", country="United States", **filters)
        return self._make_request("export.php", **params)
