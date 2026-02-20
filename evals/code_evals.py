"""Deterministic code-based evaluations."""

from agent.state import VALID_CATEGORIES, VALID_AGE_SUITABILITY

MAX_PER_CATEGORY = 5
MAX_RADIUS_MILES = 15.0
MIN_RATING = 3.5


def eval_result_count(categorized: dict) -> dict:
    """Check that each category has 0-5 results."""
    issues = []
    for cat, events in categorized.items():
        if len(events) > MAX_PER_CATEGORY:
            issues.append(f"{cat}: {len(events)} results (max {MAX_PER_CATEGORY})")
    passed = len(issues) == 0
    return {"name": "result_count", "passed": passed, "details": "; ".join(issues) if issues else "OK"}


def eval_radius_compliance(events: list[dict]) -> dict:
    """Check all events are within 15-mile radius."""
    violations = []
    for e in events:
        dist = e.get("distance_miles", 0)
        if dist > MAX_RADIUS_MILES:
            violations.append(f"{e.get('name', '?')}: {dist} miles")
    passed = len(violations) == 0
    return {"name": "radius_compliance", "passed": passed, "details": "; ".join(violations) if violations else "OK"}


def eval_cost_ordering(categorized: dict) -> dict:
    """Check that free events are listed before paid within each category."""
    issues = []
    for cat, events in categorized.items():
        seen_paid = False
        for e in events:
            if e.get("is_free"):
                if seen_paid:
                    issues.append(f"{cat}: free event '{e.get('name')}' after paid")
            else:
                seen_paid = True
    passed = len(issues) == 0
    return {"name": "cost_ordering", "passed": passed, "details": "; ".join(issues) if issues else "OK"}


def eval_rating_threshold(events: list[dict]) -> dict:
    """Check no event is below 3.5 stars."""
    violations = []
    for e in events:
        rating = e.get("rating", 0)
        if 0 < rating < MIN_RATING:
            violations.append(f"{e.get('name', '?')}: {rating}")
    passed = len(violations) == 0
    return {"name": "rating_threshold", "passed": passed, "details": "; ".join(violations) if violations else "OK"}


def eval_category_validity(events: list[dict]) -> dict:
    """Check all events have valid categories."""
    invalid = []
    for e in events:
        if e.get("category") not in VALID_CATEGORIES:
            invalid.append(f"{e.get('name', '?')}: '{e.get('category')}'")
    passed = len(invalid) == 0
    return {"name": "category_validity", "passed": passed, "details": "; ".join(invalid) if invalid else "OK"}


def eval_age_labeling(events: list[dict]) -> dict:
    """Check every event has a valid age suitability tag."""
    missing = []
    for e in events:
        if e.get("age_suitability") not in VALID_AGE_SUITABILITY:
            missing.append(f"{e.get('name', '?')}: '{e.get('age_suitability')}'")
    passed = len(missing) == 0
    return {"name": "age_labeling", "passed": passed, "details": "; ".join(missing) if missing else "OK"}


def eval_weather_consistency(mode: str, weather: dict) -> dict:
    """Check indoor/outdoor mode matches weather data."""
    is_outdoor = weather.get("is_outdoor", True)
    expected_mode = "outdoor" if is_outdoor else "indoor"
    passed = mode == expected_mode
    details = f"mode={mode}, weather.is_outdoor={is_outdoor}" if not passed else "OK"
    return {"name": "weather_consistency", "passed": passed, "details": details}


def eval_no_duplicates(events: list[dict]) -> dict:
    """Check for duplicate events by name."""
    seen = set()
    dupes = []
    for e in events:
        name = e.get("name", "").lower().strip()
        if name in seen:
            dupes.append(name)
        seen.add(name)
    passed = len(dupes) == 0
    return {"name": "no_duplicates", "passed": passed, "details": "; ".join(dupes) if dupes else "OK"}


def eval_keyword_relevance(events: list[dict], mode: str) -> dict:
    """Check activity descriptions contain relevant keywords."""
    outdoor_keywords = {"park", "hike", "outdoor", "trail", "garden", "nature", "bike", "swim", "field", "playground"}
    indoor_keywords = {"museum", "library", "class", "workshop", "art", "indoor", "center", "studio", "theater", "room"}
    target_keywords = outdoor_keywords if mode == "outdoor" else indoor_keywords

    relevant_count = 0
    for e in events:
        text = (e.get("name", "") + " " + e.get("why_recommended", "") + " " + e.get("category", "")).lower()
        if any(kw in text for kw in target_keywords):
            relevant_count += 1

    total = len(events) if events else 1
    score = relevant_count / total
    passed = score >= 0.3  # At least 30% should have mode-relevant keywords
    return {
        "name": "keyword_relevance",
        "passed": passed,
        "details": f"{relevant_count}/{total} events have {mode} keywords (score: {score:.2f})",
    }


def run_all_code_evals(state: dict) -> list[dict]:
    """Run all code-based evals on the agent state."""
    categorized = state.get("categorized_output", {})
    events = state.get("ranked_events", [])
    mode = state.get("mode", "outdoor")
    weather = state.get("weather", {})

    results = [
        eval_result_count(categorized),
        eval_radius_compliance(events),
        eval_cost_ordering(categorized),
        eval_rating_threshold(events),
        eval_category_validity(events),
        eval_age_labeling(events),
        eval_weather_consistency(mode, weather),
        eval_no_duplicates(events),
        eval_keyword_relevance(events, mode),
    ]

    for r in results:
        r["eval_type"] = "code"
        r["score"] = 1.0 if r["passed"] else 0.0

    return results
