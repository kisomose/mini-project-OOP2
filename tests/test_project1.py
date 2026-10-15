import pytest
from unittest.mock import patch, MagicMock
from src.project1 import get_coordinates, fetch_weather_forecast


@patch("src.project1.requests.get")
def test_get_coordinates_mocked_success(mock_get):
    """Test get_coordinates returns correct format with mocked response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "London",
                "country": "United Kingdom",
                "latitude": 51.5074,
                "longitude": -0.1278,
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    lat, lon, display_name = get_coordinates("London")

    assert lat == 51.5074
    assert lon == -0.1278
    assert display_name == "London, United Kingdom"


@patch("src.project1.requests.get")
def test_get_coordinates_mocked_not_found(mock_get):
    """Test get_coordinates raises ValueError when city is not found."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Location 'InvalidCityXYZ' not found."):
        get_coordinates("InvalidCityXYZ")


def test_live_get_coordinates():
    """Live API integration test for geocoding."""
    lat, lon, display_name = get_coordinates("Tokyo")
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert "Tokyo" in display_name