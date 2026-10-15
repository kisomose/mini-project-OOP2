import time
import requests
from typing import Dict, Any, Tuple, Optional

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MET_NORWAY_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

HEADERS = {
    "User-Agent": "UCU-Student-WeatherApp/1.0 (b41134@students.ucu.ac)"
}

WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


# Part C1: Custom Exception for Final Failures
class APIError(Exception):
    """Custom exception raised when an API request fails after retries."""
    pass


# Part C1: Request Wrapper with Timeout, Retry, Exponential Backoff, and Custom Exception
def safe_request(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> Dict[str, Any]:
    """Wraps requests with timeout, raise_for_status, exponential backoff, and a custom exception."""
    if headers is None:
        headers = HEADERS

    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            last_exception = e
            # Retry on connection errors or server side 5xx status codes
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code and status_code < 500 and status_code != 429:
                # Do not retry client 4xx errors (except rate limits 429)
                raise APIError(f"Client error ({status_code}) fetching {url}: {e}") from e

            if attempt < max_retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                time.sleep(sleep_time)

    raise APIError(f"API request to {url} failed after {max_retries} attempts: {last_exception}") from last_exception


def geocode(name: str, selection_index: int = 0) -> Tuple[float, float, str, str]:
    """Geocodes a location name using the safe_request wrapper."""
    params = {"name": name, "count": 10, "language": "en", "format": "json"}
    data = safe_request(GEOCODING_URL, params=params)

    results = data.get("results")
    if not results:
        raise ValueError(f"No results found for location '{name}'.")

    if selection_index >= len(results):
        selection_index = 0

    candidate = results[selection_index]
    display_name = f"{candidate.get('name')}, {candidate.get('admin1', '')} ({candidate.get('country', '')})"
    timezone = candidate.get("timezone", "auto")

    return float(candidate["latitude"]), float(candidate["longitude"]), display_name, timezone


def get_forecast(lat: float, lon: float, days: int = 7, timezone: str = "auto") -> Dict[str, Any]:
    """Requests forecast data using the safe_request wrapper."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "forecast_days": days,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "weather_code",
        ],
        "timezone": timezone,
    }
    return safe_request(FORECAST_URL, params=params)


def get_met_norway_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """Fetches secondary forecast from MET Norway using the safe_request wrapper."""
    params = {"lat": round(lat, 4), "lon": round(lon, 4)}
    return safe_request(MET_NORWAY_URL, params=params)