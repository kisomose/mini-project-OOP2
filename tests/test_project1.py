import pytest
from unittest.mock import patch, MagicMock
from src.project1 import geocode, get_forecast
import requests
from src.project1 import geocode, get_forecast, safe_request, APIError

@patch("src.project1.requests.get")
def test_geocode_mocked_success(mock_get):
    """Test geocode returns correct coordinates and formatted display name."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "London",
                "admin1": "England",
                "country": "United Kingdom",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "timezone": "Europe/London",
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    lat, lon, display_name, tz = geocode("London")

    assert lat == 51.5074
    assert lon == -0.1278
    assert "London" in display_name
    assert tz == "Europe/London"


@patch("src.project1.requests.get")
def test_geocode_mocked_not_found(mock_get):
    """Test geocode raises ValueError when city is not found or results key is empty."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="No results found for location 'InvalidCityXYZ'."):
        geocode("InvalidCityXYZ")


@patch("src.project1.requests.get")
def test_get_forecast_mocked(mock_get):
    """Test get_forecast parses daily weather data correctly."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "daily": {
            "time": ["2026-10-15"],
            "temperature_2m_max": [20.1],
            "temperature_2m_min": [12.0],
            "precipitation_sum": [0.0],
            "wind_speed_10m_max": [15.2],
            "weather_code": [0],
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = get_forecast(51.5074, -0.1278, days=1, timezone="Europe/London")

    assert "daily" in data
    assert data["daily"]["temperature_2m_max"][0] == 20.1


def test_live_geocode():
    """Live API integration test for geocoding."""
    lat, lon, display_name, tz = geocode("Tokyo")
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert "Tokyo" in display_name

@patch("src.project1.requests.get")
def test_safe_request_raises_api_error(mock_get):
    """Test that safe_request retries on failure and raises APIError on exhaustion."""
    from src.project1 import safe_request, APIError

    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    with pytest.raises(APIError, match="API request to"):
        safe_request("https://fake-url.com", max_retries=2, backoff_factor=0.01)

    assert mock_get.call_count == 2

def test_broken_inputs():
    """Test robustness against invalid city names and invalid coordinate inputs."""
    # Invalid City
    with pytest.raises(ValueError):
        geocode("NonExistentCityXYZ12389")

    # Invalid Latitude
    with pytest.raises(APIError):
        get_forecast(lat=999.0, lon=0.0)