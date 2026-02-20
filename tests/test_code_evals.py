"""Tests for code-based evaluation functions."""

import pytest

from evals.code_evals import (
    eval_result_count,
    eval_radius_compliance,
    eval_geocoding_confidence,
    eval_cost_ordering,
    eval_free_event_ratio,
    eval_rating_threshold,
    eval_rating_authenticity,
    eval_category_validity,
    eval_category_diversity,
    eval_age_labeling,
    eval_age_distribution,
    eval_weather_consistency,
    eval_no_duplicates,
    eval_keyword_relevance,
    eval_description_completeness,
    eval_url_presence,
    run_all_code_evals,
)


def _make_event(
    name="Test Event",
    category="Educational",
    distance=5.0,
    cost=0.0,
    is_free=True,
    rating=4.5,
    rating_source="Google",
    age="joint",
    why="A great educational activity for collaborative learning with other kids",
    url="https://example.com/event",
):
    return {
        "name": name,
        "category": category,
        "distance_miles": distance,
        "cost": cost,
        "is_free": is_free,
        "rating": rating,
        "rating_source": rating_source,
        "age_suitability": age,
        "why_recommended": why,
        "location_name": "Test Place",
        "address": "123 St",
        "url": url,
    }


# --- Structural checks ---

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


class TestGeocodingConfidence:
    def test_round_distances_flagged(self):
        """LLM-estimated distances are usually round numbers."""
        events = [
            _make_event(name="A", distance=5.0),
            _make_event(name="B", distance=10.0),
            _make_event(name="C", distance=3.0),
        ]
        result = eval_geocoding_confidence(events)
        assert result["passed"] is False  # All round = 0% confidence
        assert "3/3" in result["details"]

    def test_real_distances_pass(self):
        events = [
            _make_event(name="A", distance=3.7),
            _make_event(name="B", distance=8.2),
            _make_event(name="C", distance=12.1),
        ]
        result = eval_geocoding_confidence(events)
        assert result["passed"] is True

    def test_mixed_distances(self):
        events = [
            _make_event(name="A", distance=5.0),   # round
            _make_event(name="B", distance=3.7),    # real
            _make_event(name="C", distance=8.3),    # real
            _make_event(name="D", distance=10.0),   # round
        ]
        result = eval_geocoding_confidence(events)
        # 2/4 round = 50% confidence, passes (threshold 30%)
        assert result["passed"] is True

    def test_empty_events(self):
        result = eval_geocoding_confidence([])
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


class TestFreeEventRatio:
    def test_all_free_passes(self):
        events = [_make_event(is_free=True)] * 5
        result = eval_free_event_ratio(events)
        assert result["passed"] is True
        assert "100%" in result["details"]

    def test_majority_paid_fails(self):
        events = [
            _make_event(is_free=False, cost=10.0),
            _make_event(is_free=False, cost=15.0),
            _make_event(is_free=False, cost=20.0),
            _make_event(is_free=True),
        ]
        result = eval_free_event_ratio(events)
        assert result["passed"] is False  # 25% free < 50% threshold

    def test_exactly_half_passes(self):
        events = [
            _make_event(is_free=True),
            _make_event(is_free=False, cost=10.0),
        ]
        result = eval_free_event_ratio(events)
        assert result["passed"] is True

    def test_empty(self):
        result = eval_free_event_ratio([])
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


class TestRatingAuthenticity:
    def test_real_ratings_pass(self):
        events = [
            _make_event(rating=4.5, rating_source="Google"),
            _make_event(rating=4.2, rating_source="Yelp"),
        ]
        result = eval_rating_authenticity(events)
        assert result["passed"] is True

    def test_all_estimated_fails(self):
        events = [
            _make_event(rating=4.0, rating_source="estimated"),
            _make_event(rating=4.0, rating_source="estimated"),
            _make_event(rating=4.0, rating_source="estimated"),
        ]
        result = eval_rating_authenticity(events)
        assert result["passed"] is False
        assert "3/3" in result["details"]

    def test_mixed_ratings(self):
        events = [
            _make_event(rating=4.5, rating_source="Google"),
            _make_event(rating=4.0, rating_source="estimated"),
            _make_event(rating=4.3, rating_source="Yelp"),
        ]
        result = eval_rating_authenticity(events)
        assert result["passed"] is True  # 2/3 authentic = 67%

    def test_empty(self):
        result = eval_rating_authenticity([])
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


class TestCategoryDiversity:
    def test_many_categories_pass(self):
        cat = {
            "Educational": [_make_event()],
            "Sports & Fitness": [_make_event()],
            "Arts & Crafts": [_make_event()],
            "Entertainment": [_make_event()],
        }
        result = eval_category_diversity(cat)
        assert result["passed"] is True
        assert "4/6" in result["details"]

    def test_few_categories_fail(self):
        cat = {
            "Educational": [_make_event()],
            "Entertainment": [_make_event()],
        }
        result = eval_category_diversity(cat)
        assert result["passed"] is False
        assert "2/6" in result["details"]

    def test_empty_categories_not_counted(self):
        cat = {
            "Educational": [_make_event()],
            "Sports & Fitness": [],  # empty
            "Arts & Crafts": [_make_event()],
            "Entertainment": [_make_event()],
        }
        result = eval_category_diversity(cat)
        assert result["passed"] is True  # 3 populated


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


class TestAgeDistribution:
    def test_all_groups_represented(self):
        events = [
            _make_event(age="joint"),
            _make_event(age="younger"),
            _make_event(age="older"),
        ]
        result = eval_age_distribution(events)
        assert result["passed"] is True
        assert "All 3 groups" in result["details"]

    def test_only_joint_fails(self):
        """Only joint activities = 14yr old not specifically catered to."""
        events = [_make_event(age="joint")] * 5
        result = eval_age_distribution(events)
        assert result["passed"] is False
        assert "younger" in result["details"] or "older" in result["details"]

    def test_joint_plus_one_passes(self):
        events = [
            _make_event(age="joint"),
            _make_event(age="older"),
        ]
        result = eval_age_distribution(events)
        assert result["passed"] is True

    def test_missing_joint_fails(self):
        events = [
            _make_event(age="younger"),
            _make_event(age="older"),
        ]
        result = eval_age_distribution(events)
        assert result["passed"] is False

    def test_empty(self):
        result = eval_age_distribution([])
        assert result["passed"] is True


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
            _make_event(name="Nature Trail Hike", why="outdoor fun in the park"),
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


class TestDescriptionCompleteness:
    def test_good_descriptions_pass(self):
        events = [
            _make_event(why="A fantastic collaborative art workshop where kids work in teams."),
            _make_event(why="Great outdoor hike suitable for all ages with scenic views."),
        ]
        result = eval_description_completeness(events)
        assert result["passed"] is True

    def test_empty_description_flagged(self):
        events = [_make_event(why="")]
        result = eval_description_completeness(events)
        assert result["passed"] is False
        assert "empty" in result["details"]

    def test_short_description_flagged(self):
        events = [_make_event(why="Fun.")]
        result = eval_description_completeness(events)
        assert result["passed"] is False
        assert "too short" in result["details"]

    def test_allows_some_weak(self):
        """Up to 20% weak descriptions are allowed."""
        events = [
            _make_event(why="A really great collaborative art project for kids of all ages."),
            _make_event(why="Fantastic educational workshop with hands-on science experiments."),
            _make_event(why="Team-building outdoor activity that encourages social skills."),
            _make_event(why="Great scenic hike through beautiful Bay Area nature trails."),
            _make_event(why=""),  # 1 bad out of 5 = 20%, still passes
        ]
        result = eval_description_completeness(events)
        assert result["passed"] is True

    def test_empty(self):
        result = eval_description_completeness([])
        assert result["passed"] is True


class TestUrlPresence:
    def test_all_have_urls(self):
        events = [
            _make_event(url="https://example.com/1"),
            _make_event(url="https://example.com/2"),
        ]
        result = eval_url_presence(events)
        assert result["passed"] is True
        assert "100%" in result["details"]

    def test_most_missing_fails(self):
        events = [
            _make_event(url=""),
            _make_event(url=""),
            _make_event(url="https://example.com"),
        ]
        result = eval_url_presence(events)
        assert result["passed"] is False  # 33% < 70% threshold

    def test_empty(self):
        result = eval_url_presence([])
        assert result["passed"] is True


# --- Integration ---

class TestRunAllCodeEvals:
    def test_returns_16_evals(self):
        state = {
            "mode": "outdoor",
            "weather": {"is_outdoor": True},
            "ranked_events": [],
            "categorized_output": {},
        }
        results = run_all_code_evals(state)
        assert len(results) == 16

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
            assert "score" in r

    def test_gradient_scores_preserved(self):
        """New evals return gradient scores (0.0-1.0), not just binary."""
        events = [
            _make_event(name="A", age="joint", distance=5.0, rating=4.0, rating_source="estimated"),
            _make_event(name="B", age="joint", distance=10.0, rating=4.0, rating_source="estimated"),
        ]
        state = {
            "mode": "outdoor",
            "weather": {"is_outdoor": True},
            "ranked_events": events,
            "categorized_output": {"Educational": events},
        }
        results = run_all_code_evals(state)
        # Find geocoding_confidence and rating_authenticity — they should have gradient scores
        geo = next(r for r in results if r["name"] == "geocoding_confidence")
        auth = next(r for r in results if r["name"] == "rating_authenticity")
        assert isinstance(geo["score"], float)
        assert isinstance(auth["score"], float)
