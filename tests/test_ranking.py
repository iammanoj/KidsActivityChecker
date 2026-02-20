"""Tests for ranking, categorization, and event parsing logic."""

import pytest

from agent.state import VALID_CATEGORIES, VALID_AGE_SUITABILITY, Event
from agent.nodes.explain import categorize_events


# --- Event dataclass tests ---

class TestEventModel:
    def test_event_to_dict(self):
        event = Event(
            name="Art Workshop",
            category="Arts & Crafts",
            location_name="Community Center",
            address="123 Main St",
            distance_miles=2.5,
            cost=0.0,
            is_free=True,
            rating=4.5,
            rating_source="Google",
            age_suitability="joint",
            why_recommended="Great for both ages",
            url="https://example.com",
            source_query="family",
        )
        d = event.to_dict()
        assert d["name"] == "Art Workshop"
        assert d["is_free"] is True
        assert d["cost"] == 0.0
        assert d["category"] == "Arts & Crafts"

    def test_event_all_fields_present(self):
        event = Event(
            name="Test", category="Educational", location_name="", address="",
            distance_miles=0, cost=0, is_free=True, rating=4.0,
            rating_source="", age_suitability="joint", why_recommended="",
            url="", source_query="",
        )
        d = event.to_dict()
        assert len(d) == 13  # All fields present


# --- Categorization tests ---

class TestCategorizeEvents:
    def _make_event(self, name, category, rating=4.0, is_free=True, age="joint"):
        return {
            "name": name,
            "category": category,
            "rating": rating,
            "is_free": is_free,
            "age_suitability": age,
            "distance_miles": 5.0,
            "cost": 0.0 if is_free else 10.0,
            "location_name": "Test",
            "address": "123 St",
            "why_recommended": "Test reason",
            "url": "",
            "rating_source": "test",
        }

    def test_basic_categorization(self):
        events = [
            self._make_event("Museum Visit", "Educational"),
            self._make_event("Soccer", "Sports & Fitness"),
            self._make_event("Painting", "Arts & Crafts"),
        ]
        state = {"ranked_events": events}
        result = categorize_events(state)
        cat = result["categorized_output"]

        assert "Educational" in cat
        assert "Sports & Fitness" in cat
        assert "Arts & Crafts" in cat
        assert len(cat["Educational"]) == 1

    def test_max_5_per_category(self):
        events = [self._make_event(f"Event {i}", "Educational") for i in range(8)]
        state = {"ranked_events": events}
        result = categorize_events(state)
        cat = result["categorized_output"]

        assert len(cat["Educational"]) == 5

    def test_empty_categories_removed(self):
        events = [self._make_event("Hike", "Nature & Outdoor")]
        state = {"ranked_events": events}
        result = categorize_events(state)
        cat = result["categorized_output"]

        assert "Nature & Outdoor" in cat
        assert "Educational" not in cat
        assert "Entertainment" not in cat

    def test_no_events(self):
        state = {"ranked_events": []}
        result = categorize_events(state)
        assert result["categorized_output"] == {}

    def test_preserves_ranking_order(self):
        """Events within a category should maintain their ranked order."""
        events = [
            self._make_event("First", "Educational", rating=5.0),
            self._make_event("Second", "Educational", rating=4.0),
            self._make_event("Third", "Educational", rating=3.5),
        ]
        state = {"ranked_events": events}
        result = categorize_events(state)
        cat = result["categorized_output"]

        assert cat["Educational"][0]["name"] == "First"
        assert cat["Educational"][1]["name"] == "Second"
        assert cat["Educational"][2]["name"] == "Third"

    def test_multiple_age_groups(self):
        events = [
            self._make_event("Kids Art", "Arts & Crafts", age="younger"),
            self._make_event("Teen Art", "Arts & Crafts", age="older"),
            self._make_event("Family Art", "Arts & Crafts", age="joint"),
        ]
        state = {"ranked_events": events}
        result = categorize_events(state)
        cat = result["categorized_output"]

        assert len(cat["Arts & Crafts"]) == 3
        ages = [e["age_suitability"] for e in cat["Arts & Crafts"]]
        assert "younger" in ages
        assert "older" in ages
        assert "joint" in ages


# --- Constants validation ---

class TestConstants:
    def test_valid_categories(self):
        assert len(VALID_CATEGORIES) == 6
        assert "Educational" in VALID_CATEGORIES
        assert "Sports & Fitness" in VALID_CATEGORIES
        assert "Arts & Crafts" in VALID_CATEGORIES
        assert "Social & Community" in VALID_CATEGORIES
        assert "Nature & Outdoor" in VALID_CATEGORIES
        assert "Entertainment" in VALID_CATEGORIES

    def test_valid_age_suitability(self):
        assert set(VALID_AGE_SUITABILITY) == {"joint", "younger", "older"}
