import json
import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from src.project1 import geocode, get_forecast, safe_request, APIError, WMO_WEATHER_CODES

# Load offline sample JSON files from disk
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

with open(os.path.join(FIXTURES_DIR, "sample_geocode.json"), "r", encoding="utf-8") as f:
    SAMPLE_GEOCODE_JSON = json.load(f)

with open(os.path.join(FIXTURES_DIR, "sample_forecast.json"), "r", encoding="utf-8") as f:
    SAMPLE_FORECAST_JSON = json.load(f)


# --- 5 OFFLINE PARSING CHECKS USING SAMPLE JSON FILES ---

@patch("src.project1.requests.get")
def test_check_1_geocode_latitude(mock_get):
    """Check 1: Verify geocoding parses latitude correctly offline."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_GEOCODE_JSON
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    lat, _, _, _ = geocode("Kampala")
    assert lat == 0.3163


@patch("src.project1.requests.get")
def test_check_2_geocode_display_name(mock_get):
    """Check 2: Verify formatted display name construction offline."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_GEOCODE_JSON
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    _, _, display_name, _ = geocode("Kampala")
    assert "Kampala, Central Region (Uganda)" in display_name


@patch("src.project1.requests.get")
def test_check_3_forecast_temperature_parsing(mock_get):
    """Check 3: Verify parsing daily max temperature offline."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_FORECAST_JSON
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = get_forecast(0.3163, 32.5822)
    assert data["daily"]["temperature_2m_max"][0] == 25.4


@patch("src.project1.requests.get")
def test_check_4_forecast_precipitation_parsing(mock_get):
    """Check 4: Verify parsing precipitation sum offline."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_FORECAST_JSON
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = get_forecast(0.3163, 32.5822)
    assert data["daily"]["precipitation_sum"][0] == 1.2


def test_check_5_wmo_code_decoding_mapping():
    """Check 5: Verify WMO code decoding dictionary offline."""
    assert WMO_WEATHER_CODES[61] == "Slight rain"
    assert WMO_WEATHER_CODES[0] == "Clear sky"
    assert WMO_WEATHER_CODES[95] == "Thunderstorm"


# --- ERROR HANDLING AND ROBUSTNESS TESTS ---

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
def test_safe_request_raises_api_error(mock_get):
    """Test that safe_request retries on failure and raises APIError on exhaustion."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    with pytest.raises(APIError, match="API request to"):
        safe_request("https://fake-url.com", max_retries=2, backoff_factor=0.01)

    assert mock_get.call_count == 2


@patch("src.project1.requests.get")
def test_broken_inputs(mock_get):
    """Test robustness against invalid city names when mock API returns empty results."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(ValueError):
        geocode("NonExistentCityXYZ12389")