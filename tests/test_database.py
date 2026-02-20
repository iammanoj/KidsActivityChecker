"""Tests for database operations."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from db.database import (
    init_db,
    save_session,
    save_activities,
    save_feedback,
    save_eval_result,
    get_feedback_stats,
    get_eval_results,
    get_recent_sessions,
)


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    """Use a temporary database for each test."""
    db_path = tmp_path / "test.db"
    with patch("db.database.DB_PATH", db_path):
        init_db()
        yield db_path


class TestSessionOperations:
    def test_save_and_retrieve_session(self):
        session_id = save_session(
            {"city": "Los Altos", "state": "California"},
            {"temp_f": 72.0, "condition": "Clear"},
            "outdoor",
            "today",
        )
        assert session_id > 0

        sessions = get_recent_sessions(limit=1)
        assert len(sessions) == 1
        assert sessions[0]["location_city"] == "Los Altos"
        assert sessions[0]["mode"] == "outdoor"

    def test_multiple_sessions(self):
        save_session({}, {}, "indoor", "today")
        save_session({}, {}, "outdoor", "weekend")
        sessions = get_recent_sessions(limit=10)
        assert len(sessions) == 2


class TestActivityOperations:
    def test_save_activities(self):
        session_id = save_session({}, {}, "outdoor", "today")
        events = [
            {"name": "Park Hike", "category": "Nature & Outdoor", "is_free": True, "cost": 0},
            {"name": "Museum", "category": "Educational", "is_free": False, "cost": 15.0},
        ]
        ids = save_activities(session_id, events)
        assert len(ids) == 2
        assert all(isinstance(i, int) for i in ids)

    def test_save_empty_activities(self):
        session_id = save_session({}, {}, "outdoor", "today")
        ids = save_activities(session_id, [])
        assert ids == []


class TestFeedback:
    def test_save_and_get_feedback(self):
        session_id = save_session({}, {}, "outdoor", "today")
        ids = save_activities(session_id, [{"name": "Test"}])

        save_feedback(ids[0], session_id, "up")
        save_feedback(ids[0], session_id, "up")
        save_feedback(ids[0], session_id, "down")

        stats = get_feedback_stats()
        assert stats["thumbs_up"] == 2
        assert stats["thumbs_down"] == 1
        assert stats["total"] == 3
        assert stats["approval_rate"] == pytest.approx(66.7, abs=0.1)

    def test_empty_feedback_stats(self):
        stats = get_feedback_stats()
        assert stats["total"] == 0
        assert stats["approval_rate"] == 0


class TestEvalResults:
    def test_save_and_get_evals(self):
        session_id = save_session({}, {}, "outdoor", "today")

        save_eval_result(session_id, "code", "result_count", 1.0, True, "OK")
        save_eval_result(session_id, "code", "radius", 0.0, False, "Too far")
        save_eval_result(session_id, "llm_judge", "judge", 4.2, True, "{}")

        results = get_eval_results(session_id)
        assert len(results) == 3
        assert results[0]["eval_name"] == "result_count"
        assert results[0]["passed"] == 1  # SQLite stores as int
        assert results[2]["eval_type"] == "llm_judge"
