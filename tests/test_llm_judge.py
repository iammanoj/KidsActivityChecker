"""Tests for LLM judge eval."""

import json
import pytest
from unittest.mock import patch, MagicMock

from evals.llm_judge import run_llm_judge, format_activities_for_judge


class TestFormatActivities:
    def test_formats_categorized_output(self):
        categorized = {
            "Educational": [
                {
                    "name": "Museum Visit",
                    "is_free": True,
                    "cost": 0,
                    "rating": 4.5,
                    "age_suitability": "joint",
                    "distance_miles": 3.0,
                    "why_recommended": "Great learning opportunity",
                },
            ],
        }
        text = format_activities_for_judge(categorized)
        assert "Educational" in text
        assert "Museum Visit" in text
        assert "FREE" in text
        assert "4.5" in text

    def test_formats_paid_events(self):
        categorized = {
            "Entertainment": [
                {
                    "name": "Movie Night",
                    "is_free": False,
                    "cost": 12.50,
                    "rating": 4.0,
                    "age_suitability": "joint",
                    "distance_miles": 5.0,
                    "why_recommended": "Fun for all ages",
                },
            ],
        }
        text = format_activities_for_judge(categorized)
        assert "$12.50" in text

    def test_empty_categories(self):
        text = format_activities_for_judge({})
        assert text == ""


class TestRunLLMJudge:
    def test_empty_categorized_output(self):
        state = {"categorized_output": {}, "location": {}, "weather": {}, "mode": "outdoor"}
        result = run_llm_judge(state)
        assert result["passed"] is False
        assert result["score"] == 0

    @patch("evals.llm_judge.ChatOpenAI")
    def test_successful_judge_run(self, mock_llm_cls):
        """Test with mocked GPT-4o response."""
        judge_response = {
            "relevance": {"score": 4, "reasoning": "Good match"},
            "age_appropriateness": {"score": 5, "reasoning": "Great for both ages"},
            "diversity": {"score": 3, "reasoning": "OK variety"},
            "girl_friendly_appeal": {"score": 4, "reasoning": "Good options for girls"},
            "social_collaborative": {"score": 4, "reasoning": "Several group activities"},
            "description_quality": {"score": 4, "reasoning": "Helpful descriptions"},
            "overall_score": 4.0,
            "summary": "Solid recommendations.",
        }

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(judge_response))

        state = {
            "categorized_output": {
                "Educational": [
                    {
                        "name": "Museum",
                        "is_free": True,
                        "cost": 0,
                        "rating": 4.5,
                        "age_suitability": "joint",
                        "distance_miles": 3,
                        "why_recommended": "Educational fun",
                    }
                ]
            },
            "location": {"city": "Los Altos", "state": "California"},
            "weather": {"temp_f": 72, "condition": "Clear"},
            "mode": "outdoor",
            "time_mode": "today",
        }

        result = run_llm_judge(state)
        assert result["passed"] is True
        assert result["score"] == 4.0
        assert result["breakdown"]["relevance"]["score"] == 4

    @patch("evals.llm_judge.ChatOpenAI")
    def test_judge_handles_llm_error(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.side_effect = Exception("API error")

        state = {
            "categorized_output": {"Educational": [{"name": "Test", "is_free": True, "cost": 0,
                                                     "rating": 4, "age_suitability": "joint",
                                                     "distance_miles": 5, "why_recommended": "test"}]},
            "location": {"city": "Los Altos", "state": "California"},
            "weather": {"temp_f": 72, "condition": "Clear"},
            "mode": "outdoor",
            "time_mode": "today",
        }

        result = run_llm_judge(state)
        assert result["passed"] is False
        assert "error" in result["details"].lower()

    @patch("evals.llm_judge.ChatOpenAI")
    def test_judge_handles_bad_json(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="not valid json at all")

        state = {
            "categorized_output": {"Educational": [{"name": "Test", "is_free": True, "cost": 0,
                                                     "rating": 4, "age_suitability": "joint",
                                                     "distance_miles": 5, "why_recommended": "test"}]},
            "location": {"city": "Los Altos", "state": "California"},
            "weather": {"temp_f": 72, "condition": "Clear"},
            "mode": "outdoor",
            "time_mode": "today",
        }

        result = run_llm_judge(state)
        assert result["passed"] is False
