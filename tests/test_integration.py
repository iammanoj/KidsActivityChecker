"""Integration tests — test the full pipeline end-to-end with mocks."""

import json
import pytest
from unittest.mock import patch, MagicMock

from agent.graph import run_activity_tracker, build_graph
from agent.state import VALID_CATEGORIES, VALID_AGE_SUITABILITY


# Fixtures for realistic mock data

MOCK_WEATHER = {
    "temp_f": 75.0,
    "condition": "Clear",
    "description": "clear sky",
    "weather_id": 800,
    "is_outdoor": True,
    "humidity": 40,
    "wind_mph": 5.0,
}

MOCK_SEARCH_RESULTS = [
    {"title": "Los Altos Nature Trail Hike", "url": "https://example.com/hike",
     "content": "Family-friendly hiking trail in Rancho San Antonio. Free. Great for all ages. 4.5 stars on Google."},
    {"title": "Bay Area Discovery Museum", "url": "https://example.com/museum",
     "content": "Interactive science museum for kids. $15 admission. Located in Sausalito. Rated 4.7."},
    {"title": "Community Art Workshop for Girls", "url": "https://example.com/art",
     "content": "Free art class at Los Altos Library. Perfect for ages 8-15. Collaborative project."},
    {"title": "Youth Soccer Clinic", "url": "https://example.com/soccer",
     "content": "Free soccer clinic at Egan Junior High. Ages 8-14. Teamwork-focused. Rating: 4.3."},
    {"title": "Teen Coding Workshop", "url": "https://example.com/coding",
     "content": "Python coding for teens 12-16. Free at Mountain View Library. Rated 4.6."},
]

MOCK_RANKED_EVENTS = [
    {
        "name": "Los Altos Nature Trail Hike",
        "category": "Nature & Outdoor",
        "location_name": "Rancho San Antonio",
        "address": "22500 Cristo Rey Dr, Los Altos",
        "distance_miles": 3.2,
        "cost": 0.0,
        "is_free": True,
        "rating": 4.5,
        "rating_source": "Google",
        "age_suitability": "joint",
        "why_recommended": "Perfect family hike accessible to both ages with beautiful nature.",
        "url": "https://example.com/hike",
        "source_query": "family",
    },
    {
        "name": "Community Art Workshop",
        "category": "Arts & Crafts",
        "location_name": "Los Altos Library",
        "address": "13 S San Antonio Rd, Los Altos",
        "distance_miles": 1.0,
        "cost": 0.0,
        "is_free": True,
        "rating": 4.2,
        "rating_source": "estimated",
        "age_suitability": "joint",
        "why_recommended": "Free collaborative art project perfect for girls ages 8-15.",
        "url": "https://example.com/art",
        "source_query": "family",
    },
    {
        "name": "Youth Soccer Clinic",
        "category": "Sports & Fitness",
        "location_name": "Egan Junior High",
        "address": "100 W Portola Ave, Los Altos",
        "distance_miles": 2.0,
        "cost": 0.0,
        "is_free": True,
        "rating": 4.3,
        "rating_source": "estimated",
        "age_suitability": "joint",
        "why_recommended": "Team-building soccer for ages 8-14, great for meeting other kids.",
        "url": "https://example.com/soccer",
        "source_query": "family",
    },
    {
        "name": "Teen Coding Workshop",
        "category": "Educational",
        "location_name": "Mountain View Library",
        "address": "585 Franklin St, Mountain View",
        "distance_miles": 5.0,
        "cost": 0.0,
        "is_free": True,
        "rating": 4.6,
        "rating_source": "Google",
        "age_suitability": "older",
        "why_recommended": "Python coding class perfect for the 14-year-old, collaborative learning.",
        "url": "https://example.com/coding",
        "source_query": "teens_14",
    },
]


class TestBuildGraph:
    def test_graph_compiles(self):
        """The graph should compile without errors."""
        graph = build_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        """Verify all pipeline nodes exist."""
        graph = build_graph()
        # LangGraph compiled graph has a .nodes attribute
        node_names = set(graph.get_graph().nodes.keys())
        expected = {"detect_location", "check_weather", "search_activities",
                    "rank_and_parse", "categorize_events"}
        assert expected.issubset(node_names)


class TestEndToEndPipeline:
    """Full pipeline integration test with all external calls mocked."""

    @patch("agent.nodes.rank.ChatOpenAI")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    @patch("agent.nodes.weather.get_weather")
    @patch("agent.nodes.location.requests.get")
    def test_full_pipeline_outdoor(
        self, mock_ip, mock_weather, mock_search, mock_paid, mock_llm_cls
    ):
        # Mock IP geolocation
        mock_ip.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "status": "success",
                "city": "Los Altos",
                "regionName": "California",
                "lat": 37.37,
                "lon": -122.10,
            },
        )
        mock_ip.return_value.raise_for_status = MagicMock()

        # Mock weather
        mock_weather.return_value = MOCK_WEATHER

        # Mock search
        mock_search.return_value = MOCK_SEARCH_RESULTS[:2]
        mock_paid.return_value = []

        # Mock Claude LLM for ranking
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(
            content=json.dumps(MOCK_RANKED_EVENTS)
        )

        result = run_activity_tracker(time_mode="today")

        # Verify pipeline produced complete output
        assert result["location"]["city"] == "Los Altos"
        assert result["mode"] == "outdoor"
        assert result["weather"]["temp_f"] == 75.0
        assert len(result["ranked_events"]) > 0
        assert len(result["categorized_output"]) > 0

        # Verify categorization is valid
        for cat in result["categorized_output"]:
            assert cat in VALID_CATEGORIES
            assert len(result["categorized_output"][cat]) <= 5

        # Verify all events have required fields
        for event in result["ranked_events"]:
            assert "name" in event
            assert "category" in event
            assert event["age_suitability"] in VALID_AGE_SUITABILITY
            assert event["rating"] >= 3.5

    @patch("agent.nodes.rank.ChatOpenAI")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    @patch("agent.nodes.weather.get_weather")
    def test_full_pipeline_indoor(
        self, mock_weather, mock_search, mock_paid, mock_llm_cls
    ):
        """Test pipeline in indoor mode with location override."""
        mock_weather.return_value = {
            "temp_f": 50.0,
            "condition": "Rain",
            "description": "light rain",
            "weather_id": 500,
            "is_outdoor": False,
            "humidity": 80,
            "wind_mph": 10.0,
        }

        mock_search.return_value = [
            {"title": "Library Storytime", "url": "https://example.com",
             "content": "Free storytime for kids at the library."}
        ]
        mock_paid.return_value = []

        indoor_events = [
            {
                "name": "Library Storytime",
                "category": "Educational",
                "location_name": "Los Altos Library",
                "address": "13 S San Antonio Rd",
                "distance_miles": 1.0,
                "cost": 0.0,
                "is_free": True,
                "rating": 4.0,
                "rating_source": "estimated",
                "age_suitability": "younger",
                "why_recommended": "Fun storytime for younger kids.",
                "url": "https://example.com",
                "source_query": "kids_8",
            }
        ]

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(indoor_events))

        result = run_activity_tracker(
            time_mode="weekend",
            location_override={"city": "Los Altos", "state": "California", "lat": 37.37, "lon": -122.10},
        )

        assert result["mode"] == "indoor"
        assert result["time_mode"] == "weekend"
        assert result["location"]["city"] == "Los Altos"

    @patch("agent.nodes.rank.ChatOpenAI")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    @patch("agent.nodes.weather.get_weather")
    def test_pipeline_handles_no_search_results(
        self, mock_weather, mock_search, mock_paid, mock_llm_cls
    ):
        """Pipeline should gracefully handle zero search results."""
        mock_weather.return_value = MOCK_WEATHER
        mock_search.return_value = []
        mock_paid.return_value = []

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="[]")

        result = run_activity_tracker(
            time_mode="today",
            location_override={"city": "Los Altos", "state": "California", "lat": 37.37, "lon": -122.10},
        )

        assert result["ranked_events"] == []
        assert result["categorized_output"] == {}


class TestEvalIntegration:
    """Test that evals work correctly on pipeline output."""

    def test_code_evals_on_good_output(self):
        """Code evals should mostly pass on well-formed output."""
        from evals.code_evals import run_all_code_evals

        state = {
            "mode": "outdoor",
            "weather": {"is_outdoor": True},
            "ranked_events": MOCK_RANKED_EVENTS,
            "categorized_output": {},
        }

        # Build proper categorization
        from agent.nodes.explain import categorize_events
        state = categorize_events(state)

        results = run_all_code_evals(state)

        passed = [r for r in results if r["passed"]]
        failed = [r for r in results if not r["passed"]]

        # At least 7 of 9 should pass on clean mock data
        assert len(passed) >= 7, f"Failed evals: {[r['name'] for r in failed]}"

    def test_code_evals_on_bad_output(self):
        """Code evals should catch issues in malformed output."""
        from evals.code_evals import run_all_code_evals

        bad_events = [
            {
                "name": "Bad Event",
                "category": "InvalidCategory",
                "distance_miles": 25.0,  # Too far
                "rating": 2.0,  # Too low
                "is_free": True,
                "cost": 0,
                "age_suitability": "toddler",  # Invalid
                "why_recommended": "",
                "location_name": "",
                "address": "",
                "url": "",
                "rating_source": "",
            }
        ]

        state = {
            "mode": "indoor",
            "weather": {"is_outdoor": True},  # Inconsistent!
            "ranked_events": bad_events,
            "categorized_output": {"InvalidCategory": bad_events},
        }

        results = run_all_code_evals(state)
        failed = [r for r in results if not r["passed"]]

        # Should catch: radius, rating, category, age_labeling, weather_consistency
        failed_names = {r["name"] for r in failed}
        assert "radius_compliance" in failed_names
        assert "rating_threshold" in failed_names
        assert "category_validity" in failed_names
        assert "age_labeling" in failed_names
        assert "weather_consistency" in failed_names
