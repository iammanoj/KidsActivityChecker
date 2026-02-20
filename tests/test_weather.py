"""Tests for weather decision logic."""

import pytest
from unittest.mock import patch, MagicMock

from agent.tools.weather_tool import get_weather, OUTDOOR_TEMP_THRESHOLD_F, RAIN_CODES
from agent.nodes.weather import check_weather


# --- Unit tests for weather_tool ---

class TestWeatherThresholds:
    """Test the indoor/outdoor decision logic."""

    def _mock_weather_response(self, temp_f, weather_id, condition="Clear"):
        return {
            "main": {"temp": temp_f, "humidity": 50},
            "weather": [{"id": weather_id, "main": condition, "description": "test"}],
            "wind": {"speed": 5.0},
        }

    @patch("agent.tools.weather_tool.requests.get")
    @patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "test_key"})
    def test_warm_sunny_is_outdoor(self, mock_get):
        """65°F+ and clear sky => outdoor mode."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_weather_response(75.0, 800, "Clear"),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = get_weather(37.37, -122.10)
        assert result["is_outdoor"] is True
        assert result["temp_f"] == 75.0

    @patch("agent.tools.weather_tool.requests.get")
    @patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "test_key"})
    def test_cold_is_indoor(self, mock_get):
        """Below 65°F => indoor mode."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_weather_response(55.0, 800, "Clear"),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = get_weather(37.37, -122.10)
        assert result["is_outdoor"] is False
        assert result["temp_f"] == 55.0

    @patch("agent.tools.weather_tool.requests.get")
    @patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "test_key"})
    def test_rainy_warm_is_indoor(self, mock_get):
        """Warm but rainy => indoor mode."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_weather_response(80.0, 500, "Rain"),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = get_weather(37.37, -122.10)
        assert result["is_outdoor"] is False

    @patch("agent.tools.weather_tool.requests.get")
    @patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "test_key"})
    def test_exactly_65_is_outdoor(self, mock_get):
        """Exactly 65°F and clear => outdoor (threshold is >=)."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_weather_response(65.0, 800, "Clear"),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = get_weather(37.37, -122.10)
        assert result["is_outdoor"] is True

    @patch("agent.tools.weather_tool.requests.get")
    @patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "test_key"})
    def test_snow_is_indoor(self, mock_get):
        """Snow weather code => indoor."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_weather_response(70.0, 601, "Snow"),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = get_weather(37.37, -122.10)
        assert result["is_outdoor"] is False

    def test_missing_api_key_falls_back_to_open_meteo(self):
        """With no OWM key, should fall back to Open-Meteo and still return weather."""
        with patch.dict("os.environ", {}, clear=True):
            result = get_weather(37.37, -122.10)
            assert "temp_f" in result
            assert "is_outdoor" in result


# --- Tests for weather node ---

class TestCheckWeatherNode:
    """Test the LangGraph weather node."""

    @patch("agent.nodes.weather.get_weather")
    def test_node_sets_outdoor_mode(self, mock_weather):
        mock_weather.return_value = {
            "temp_f": 72.0,
            "condition": "Clear",
            "description": "clear sky",
            "is_outdoor": True,
            "humidity": 45,
            "wind_mph": 3.0,
        }

        state = {"location": {"city": "Los Altos", "state": "CA", "lat": 37.37, "lon": -122.10}}
        result = check_weather(state)

        assert result["mode"] == "outdoor"
        assert result["weather"]["temp_f"] == 72.0

    @patch("agent.nodes.weather.get_weather")
    def test_node_sets_indoor_mode(self, mock_weather):
        mock_weather.return_value = {
            "temp_f": 50.0,
            "condition": "Rain",
            "description": "light rain",
            "is_outdoor": False,
            "humidity": 80,
            "wind_mph": 10.0,
        }

        state = {"location": {"city": "Los Altos", "state": "CA", "lat": 37.37, "lon": -122.10}}
        result = check_weather(state)

        assert result["mode"] == "indoor"

    @patch("agent.nodes.weather.get_weather")
    def test_node_handles_api_error(self, mock_weather):
        """On API failure, should default to outdoor mode."""
        mock_weather.side_effect = Exception("API down")

        state = {"location": {"city": "Los Altos", "state": "CA", "lat": 37.37, "lon": -122.10}}
        result = check_weather(state)

        assert result["mode"] == "outdoor"
        assert "error" in result


class TestRainCodes:
    """Verify rain code ranges cover expected weather conditions."""

    def test_thunderstorm_codes_in_range(self):
        for code in [200, 201, 210, 221, 230]:
            assert code in RAIN_CODES

    def test_drizzle_codes_in_range(self):
        for code in [300, 301, 310, 321]:
            assert code in RAIN_CODES

    def test_rain_codes_in_range(self):
        for code in [500, 501, 502, 511, 520]:
            assert code in RAIN_CODES

    def test_snow_codes_in_range(self):
        for code in [600, 601, 602, 611, 620]:
            assert code in RAIN_CODES

    def test_clear_not_in_range(self):
        assert 800 not in RAIN_CODES
        assert 801 not in RAIN_CODES
