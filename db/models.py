"""SQLite schema definitions."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location_city TEXT,
    location_state TEXT,
    weather_temp_f REAL,
    weather_condition TEXT,
    mode TEXT,
    time_mode TEXT
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    location_name TEXT,
    address TEXT,
    distance_miles REAL,
    cost REAL,
    is_free BOOLEAN,
    rating REAL,
    rating_source TEXT,
    age_suitability TEXT,
    why_recommended TEXT,
    url TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    vote TEXT NOT NULL CHECK(vote IN ('up', 'down')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS eval_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    eval_type TEXT NOT NULL,
    eval_name TEXT,
    score REAL,
    passed BOOLEAN,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
"""
