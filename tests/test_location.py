"""Tests for location detection node."""

import pytest
from unittest.mock import patch, MagicMock

from agent.nodes.location import detect_location, DEFAULT_LOCATION


class TestDetectLocation:
    def test_uses_override_if_provided(self):
        """If location already in state, skip detection."""
        override = {"city": "Palo Alto", "state": "CA", "lat": 37.44, "lon": -122.14}
        state = {"location": override}
        result = detect_location(state)
        assert result["location"]["city"] == "Palo Alto"

    @patch("agent.nodes.location.requests.get")
    def test_ip_detection_success(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "status": "success",
                "city": "San Jose",
                "regionName": "California",
                "lat": 37.34,
                "lon": -121.89,
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()

        state = {}
        result = detect_location(state)
        assert result["location"]["city"] == "San Jose"
        assert result["location"]["lat"] == 37.34

    @patch("agent.nodes.location.requests.get")
    def test_ip_detection_failure_falls_back(self, mock_get):
        """On IP API failure, use default Los Altos location."""
        mock_get.side_effect = Exception("Network error")

        state = {}
        result = detect_location(state)
        assert result["location"] == DEFAULT_LOCATION
        assert result["location"]["city"] == "Los Altos"

    @patch("agent.nodes.location.requests.get")
    def test_ip_api_returns_fail_status(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "fail", "message": "reserved range"},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        state = {}
        result = detect_location(state)
        assert result["location"] == DEFAULT_LOCATION

    def test_default_location_is_los_altos(self):
        assert DEFAULT_LOCATION["city"] == "Los Altos"
        assert DEFAULT_LOCATION["state"] == "California"
        assert abs(DEFAULT_LOCATION["lat"] - 37.3685) < 0.01
