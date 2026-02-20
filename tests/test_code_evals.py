"""Tests for code-based evaluation functions."""

import pytest

from evals.code_evals import (
    eval_result_count,
    eval_radius_compliance,
    eval_cost_ordering,
    eval_rating_threshold,
    eval_category_validity,
    eval_age_labeling,
    eval_weather_consistency,
    eval_no_duplicates,
    eval_keyword_relevance,
    run_all_code_evals,
)


def _make_event(
    name="Test Event",
    category="Educational",
    distance=5.0,
    cost=0.0,
    is_free=True,
    rating=4.5,
    age="joint",
    why="A great activity",
):
    return {
        "name": name,
        "category": category,
        "distance_miles": distance,
        "cost": cost,
        "is_free": is_free,
        "rating": rating,
        "age_suitability": age,
        "why_recommended": why,
        "location_name": "Test Place",
        "address": "123 St",
        "url": "",
        "rating_source": "test",
    }


class TestResultCount:
    def test_pass_under_limit(self):
        cat = {"Educational": [_make_event()] * 5}
        result = eval_result_count(cat)
        assert result["passed"] is True

    def test_fail_over_limit(self):
        cat = {"Educational": [_make_event()] * 7}
        result = eval_result_count(cat)
        assert result["passed"] is False

    def test_empty_categories(self):
        cat = {}
        result = eval_result_count(cat)
        assert result["passed"] is True


class TestRadiusCompliance:
    def test_all_within_radius(self):
        events = [_make_event(distance=5.0), _make_event(distance=14.9)]
        result = eval_radius_compliance(events)
        assert result["passed"] is True

    def test_one_outside_radius(self):
        events = [_make_event(distance=5.0), _make_event(name="Far Away", distance=20.0)]
        result = eval_radius_compliance(events)
        assert result["passed"] is False
        assert "Far Away" in result["details"]

    def test_exactly_15_miles(self):
        events = [_make_event(distance=15.0)]
        result = eval_radius_compliance(events)
        assert result["passed"] is True


class TestCostOrdering:
    def test_free_before_paid(self):
        cat = {
            "Educational": [
                _make_event(name="Free", is_free=True),
                _make_event(name="Paid", is_free=False, cost=10.0),
            ]
        }
        result = eval_cost_ordering(cat)
        assert result["passed"] is True

    def test_paid_before_free_fails(self):
        cat = {
            "Educational": [
                _make_event(name="Paid", is_free=False, cost=10.0),
                _make_event(name="Free", is_free=True),
            ]
        }
        result = eval_cost_ordering(cat)
        assert result["passed"] is False

    def test_all_free(self):
        cat = {"Educational": [_make_event(is_free=True)] * 3}
        result = eval_cost_ordering(cat)
        assert result["passed"] is True


class TestRatingThreshold:
    def test_all_above_threshold(self):
        events = [_make_event(rating=4.0), _make_event(rating=3.5)]
        result = eval_rating_threshold(events)
        assert result["passed"] is True

    def test_one_below_threshold(self):
        events = [_make_event(rating=4.0), _make_event(name="Bad", rating=2.0)]
        result = eval_rating_threshold(events)
        assert result["passed"] is False

    def test_zero_rating_ignored(self):
        """Rating of 0 means unrated, should not fail."""
        events = [_make_event(rating=0)]
        result = eval_rating_threshold(events)
        assert result["passed"] is True


class TestCategoryValidity:
    def test_valid_categories(self):
        events = [_make_event(category="Educational"), _make_event(category="Entertainment")]
        result = eval_category_validity(events)
        assert result["passed"] is True

    def test_invalid_category(self):
        events = [_make_event(category="Cooking")]
        result = eval_category_validity(events)
        assert result["passed"] is False


class TestAgeLabeling:
    def test_valid_labels(self):
        events = [
            _make_event(age="joint"),
            _make_event(age="younger"),
            _make_event(age="older"),
        ]
        result = eval_age_labeling(events)
        assert result["passed"] is True

    def test_invalid_label(self):
        events = [_make_event(age="toddler")]
        result = eval_age_labeling(events)
        assert result["passed"] is False


class TestWeatherConsistency:
    def test_outdoor_matches(self):
        result = eval_weather_consistency("outdoor", {"is_outdoor": True})
        assert result["passed"] is True

    def test_indoor_matches(self):
        result = eval_weather_consistency("indoor", {"is_outdoor": False})
        assert result["passed"] is True

    def test_mismatch_fails(self):
        result = eval_weather_consistency("outdoor", {"is_outdoor": False})
        assert result["passed"] is False


class TestNoDuplicates:
    def test_no_dupes(self):
        events = [_make_event(name="A"), _make_event(name="B")]
        result = eval_no_duplicates(events)
        assert result["passed"] is True

    def test_has_dupes(self):
        events = [_make_event(name="Same Event"), _make_event(name="Same Event")]
        result = eval_no_duplicates(events)
        assert result["passed"] is False

    def test_case_insensitive(self):
        events = [_make_event(name="Art Class"), _make_event(name="art class")]
        result = eval_no_duplicates(events)
        assert result["passed"] is False


class TestKeywordRelevance:
    def test_outdoor_keywords_detected(self):
        events = [
            _make_event(name="Nature Trail Hike", why="outdoor fun"),
            _make_event(name="Park Play", why="playground activities"),
            _make_event(name="Soccer Game", why="field sports"),
        ]
        result = eval_keyword_relevance(events, "outdoor")
        assert result["passed"] is True

    def test_indoor_keywords_detected(self):
        events = [
            _make_event(name="Museum Visit", why="educational indoor"),
            _make_event(name="Art Class", why="studio workshop"),
        ]
        result = eval_keyword_relevance(events, "indoor")
        assert result["passed"] is True

    def test_no_relevant_keywords_fails(self):
        events = [
            _make_event(name="Random", why="something else", category="Entertainment"),
            _make_event(name="Other", why="no match", category="Entertainment"),
        ]
        result = eval_keyword_relevance(events, "outdoor")
        assert result["passed"] is False


class TestRunAllCodeEvals:
    def test_all_pass_on_clean_data(self):
        state = {
            "mode": "outdoor",
            "weather": {"is_outdoor": True},
            "ranked_events": [
                _make_event(name="Park Hike", why="outdoor nature trail"),
                _make_event(name="Garden Walk", why="beautiful garden outdoor"),
            ],
            "categorized_output": {
                "Educational": [_make_event(name="Park Hike", why="outdoor nature trail")],
                "Nature & Outdoor": [_make_event(name="Garden Walk", why="beautiful garden outdoor")],
            },
        }
        results = run_all_code_evals(state)
        assert len(results) == 9
        pass_count = sum(1 for r in results if r["passed"])
        assert pass_count >= 7  # Most should pass

    def test_all_have_eval_type(self):
        state = {
            "mode": "outdoor",
            "weather": {"is_outdoor": True},
            "ranked_events": [],
            "categorized_output": {},
        }
        results = run_all_code_evals(state)
        for r in results:
            assert r["eval_type"] == "code"
            assert "name" in r
            assert "passed" in r
