"""SQLite database operations."""

import json
import sqlite3
from pathlib import Path

from .models import SCHEMA_SQL

DB_PATH = Path(__file__).parent.parent / "kids_activity.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def save_session(location: dict, weather: dict, mode: str, time_mode: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO sessions (location_city, location_state, weather_temp_f,
           weather_condition, mode, time_mode)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            location.get("city", ""),
            location.get("state", ""),
            weather.get("temp_f", 0),
            weather.get("condition", ""),
            mode,
            time_mode,
        ),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def save_activities(session_id: int, events: list[dict]) -> list[int]:
    conn = get_connection()
    activity_ids = []
    for event in events:
        cursor = conn.execute(
            """INSERT INTO activities (session_id, name, category, location_name,
               address, distance_miles, cost, is_free, rating, rating_source,
               age_suitability, why_recommended, url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                event.get("name", ""),
                event.get("category", ""),
                event.get("location_name", ""),
                event.get("address", ""),
                event.get("distance_miles", 0),
                event.get("cost", 0),
                event.get("is_free", True),
                event.get("rating", 0),
                event.get("rating_source", ""),
                event.get("age_suitability", "joint"),
                event.get("why_recommended", ""),
                event.get("url", ""),
            ),
        )
        activity_ids.append(cursor.lastrowid)
    conn.commit()
    conn.close()
    return activity_ids


def save_feedback(activity_id: int, session_id: int, vote: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO feedback (activity_id, session_id, vote) VALUES (?, ?, ?)",
        (activity_id, session_id, vote),
    )
    conn.commit()
    conn.close()


def save_eval_result(
    session_id: int, eval_type: str, eval_name: str, score: float, passed: bool, details: str
):
    conn = get_connection()
    conn.execute(
        """INSERT INTO eval_results (session_id, eval_type, eval_name, score, passed, details)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, eval_type, eval_name, score, passed, details),
    )
    conn.commit()
    conn.close()


def get_feedback_stats(session_id: int | None = None) -> dict:
    conn = get_connection()
    where = "WHERE session_id = ?" if session_id else ""
    params = (session_id,) if session_id else ()

    up = conn.execute(
        f"SELECT COUNT(*) FROM feedback {where} {'AND' if where else 'WHERE'} vote='up'",
        params,
    ).fetchone()[0]
    down = conn.execute(
        f"SELECT COUNT(*) FROM feedback {where} {'AND' if where else 'WHERE'} vote='down'",
        params,
    ).fetchone()[0]
    conn.close()

    total = up + down
    return {
        "thumbs_up": up,
        "thumbs_down": down,
        "total": total,
        "approval_rate": round(up / total * 100, 1) if total > 0 else 0,
    }


def get_eval_results(session_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM eval_results WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_sessions(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
