import requests
from typing import Dict, Any, Tuple

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

def get_coordinates(location_name: str) -> Tuple[float, float, str]:
    """Resolves a city name to latitude, longitude, and formatted name.
    
    Args:
        location_name: The target city or region name.
        
    Returns:
        A tuple of (latitude, longitude, resolved_location_name).
    """
    params = {"name": location_name, "count": 1, "language": "en", "format": "json"}
    response = requests.get(GEOCODING_URL, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    if not data.get("results"):
        raise ValueError(f"Location '{location_name}' not found.")
        
    result = data["results"][0]
    display_name = f"{result['name']}, {result.get('country', '')}"
    return result["latitude"], result["longitude"], display_name


def fetch_weather_forecast(lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
    """Fetches daily weather forecast data for given coordinates.
    
    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        days: Forecast length in days (1-16).
        
    Returns:
        Dictionary containing daily forecast parameters.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "forecast_days": days,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max"
        ],
        "timezone": "auto"
    }
    response = requests.get(FORECAST_URL, params=params, timeout=10)
    response.raise_for_status()
    
    return response.json()
