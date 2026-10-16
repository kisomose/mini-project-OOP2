import time
import requests
from typing import Dict, Any, Tuple, Optional

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Drizzle: Light",
    53: "Drizzle: Moderate",
    55: "Drizzle: Dense intensity",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Rain showers: Slight",
    81: "Rain showers: Moderate",
    82: "Rain showers: Violent",
    95: "Thunderstorm",
}


class APIError(Exception):
    """Custom exception raised when an API request fails after retries."""
    pass


def safe_request(url: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0, max_retries: int = 3, backoff_factor: float = 0.5) -> Dict[str, Any]:
    """Helper wrapper to make robust GET requests with retries and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise APIError(f"API request to {url} failed: {e}")
            time.sleep(backoff_factor * (2 ** attempt))


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
    """Fetches weather forecast data for coordinates using Open-Meteo API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "weather_code",
        ],
        "forecast_days": days,
        "timezone": timezone,
    }
    return safe_request(FORECAST_URL, params=params)