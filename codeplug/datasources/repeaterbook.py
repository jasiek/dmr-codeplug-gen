import requests
from .cache import FileCache


class RepeaterBookAPI(FileCache):
    """
    RepeaterBook API data source

    Provides access to repeater data from RepeaterBook.com
    Supports both North America and international repeaters
    """

    def __init__(self, user_agent="dmr-codeplug-gen, test@example.com"):
        FileCache.__init__(self, "repeaterbook")
        self.user_agent = user_agent
        self.base_url = "https://www.repeaterbook.com/api"

    def _get_headers(self):
        """Get required headers including User-Agent for API authentication"""
        return {"User-Agent": self.user_agent}

    def _build_params(self, **kwargs):
        """Build query parameters, filtering out None values"""
        return {k: v for k, v in kwargs.items() if v is not None}

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
            return self.method.loads(content)
        else:
            # Make request with headers
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            content = response.json()
            self.write_cache(cache_key, content)
            return content

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
