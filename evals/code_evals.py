"""Deterministic code-based evaluations."""

import math

from agent.state import VALID_CATEGORIES, VALID_AGE_SUITABILITY

MAX_PER_CATEGORY = 5
MAX_RADIUS_MILES = 15.0
MIN_RATING = 3.5
MIN_FREE_RATIO = 0.5  # At least 50% of events should be free
MIN_CATEGORY_COUNT = 3  # At least 3 of 6 categories should have events
DEFAULT_RATING_VALUE = 4.0  # LLM's default when no real rating exists


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


def eval_geocoding_confidence(events: list[dict]) -> dict:
    """Flag events where distance is likely LLM-estimated (round numbers, suspicious patterns).

    LLMs tend to produce round distances (5.0, 10.0, 3.0) when guessing.
    Real geocoded distances are almost never whole numbers.
    """
    if not events:
        return {"name": "geocoding_confidence", "passed": True, "details": "No events to check"}

    suspicious = 0
    total = len(events)
    for e in events:
        dist = e.get("distance_miles", 0)
        # Flag if distance is a whole number or ends in .0 or .5 (likely estimated)
        if dist > 0 and (dist == int(dist) or dist * 2 == int(dist * 2)):
            suspicious += 1

    confidence = 1.0 - (suspicious / total) if total > 0 else 1.0
    passed = confidence >= 0.3  # Pass if at least 30% seem real (lenient for MVP)
    return {
        "name": "geocoding_confidence",
        "passed": passed,
        "score_detail": round(confidence, 2),
        "details": f"{suspicious}/{total} events have round distances (confidence: {confidence:.0%}). "
                   f"Distances are likely LLM-estimated, not geocoded.",
    }


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


def eval_free_event_ratio(events: list[dict]) -> dict:
    """Check that free events make up at least 50% of recommendations.

    Core priority: the app should prioritize free events.
    """
    if not events:
        return {"name": "free_event_ratio", "passed": True, "details": "No events"}

    free_count = sum(1 for e in events if e.get("is_free"))
    total = len(events)
    ratio = free_count / total

    passed = ratio >= MIN_FREE_RATIO
    return {
        "name": "free_event_ratio",
        "passed": passed,
        "score_detail": round(ratio, 2),
        "details": f"{free_count}/{total} events are free ({ratio:.0%}). Target: >={MIN_FREE_RATIO:.0%}",
    }


def eval_rating_threshold(events: list[dict]) -> dict:
    """Check no event is below 3.5 stars."""
    violations = []
    for e in events:
        rating = e.get("rating", 0)
        if 0 < rating < MIN_RATING:
            violations.append(f"{e.get('name', '?')}: {rating}")
    passed = len(violations) == 0
    return {"name": "rating_threshold", "passed": passed, "details": "; ".join(violations) if violations else "OK"}


def eval_rating_authenticity(events: list[dict]) -> dict:
    """Flag events where ratings appear to be LLM-estimated rather than from real sources.

    LLMs default to 4.0 and use 'estimated' as source. Real ratings come from
    Google, Yelp, TripAdvisor, etc. and are rarely exactly 4.0.
    """
    if not events:
        return {"name": "rating_authenticity", "passed": True, "details": "No events"}

    estimated_count = 0
    for e in events:
        source = e.get("rating_source", "").lower()
        rating = e.get("rating", 0)
        # Flag if source says "estimated" or rating is exactly the default
        if "estimated" in source or "estimate" in source:
            estimated_count += 1
        elif rating == DEFAULT_RATING_VALUE and not source:
            estimated_count += 1

    total = len(events)
    authentic_ratio = 1.0 - (estimated_count / total) if total > 0 else 1.0
    passed = authentic_ratio >= 0.3  # At least 30% should have real ratings
    return {
        "name": "rating_authenticity",
        "passed": passed,
        "score_detail": round(authentic_ratio, 2),
        "details": f"{estimated_count}/{total} ratings are LLM-estimated (authenticity: {authentic_ratio:.0%}). "
                   f"Consider adding real review data from Google/Yelp.",
    }


def eval_category_validity(events: list[dict]) -> dict:
    """Check all events have valid categories."""
    invalid = []
    for e in events:
        if e.get("category") not in VALID_CATEGORIES:
            invalid.append(f"{e.get('name', '?')}: '{e.get('category')}'")
    passed = len(invalid) == 0
    return {"name": "category_validity", "passed": passed, "details": "; ".join(invalid) if invalid else "OK"}


def eval_category_diversity(categorized: dict) -> dict:
    """Check that events span at least 3 of the 6 categories.

    A good recommendation set should have variety, not cluster in 1-2 categories.
    """
    populated = [cat for cat, events in categorized.items() if events]
    count = len(populated)
    total = len(VALID_CATEGORIES)

    passed = count >= MIN_CATEGORY_COUNT
    return {
        "name": "category_diversity",
        "passed": passed,
        "score_detail": count,
        "details": f"{count}/{total} categories populated: {', '.join(populated) if populated else 'none'}. "
                   f"Target: >={MIN_CATEGORY_COUNT}",
    }


def eval_age_labeling(events: list[dict]) -> dict:
    """Check every event has a valid age suitability tag."""
    missing = []
    for e in events:
        if e.get("age_suitability") not in VALID_AGE_SUITABILITY:
            missing.append(f"{e.get('name', '?')}: '{e.get('age_suitability')}'")
    passed = len(missing) == 0
    return {"name": "age_labeling", "passed": passed, "details": "; ".join(missing) if missing else "OK"}


def eval_age_distribution(events: list[dict]) -> dict:
    """Check that all age groups are represented in recommendations.

    The live test showed the 14-year-old was underserved — this eval catches that.
    At minimum, 'joint' and at least one of 'younger'/'older' should be present.
    """
    if not events:
        return {"name": "age_distribution", "passed": True, "details": "No events"}

    age_groups = set(e.get("age_suitability") for e in events)
    has_joint = "joint" in age_groups
    has_younger = "younger" in age_groups
    has_older = "older" in age_groups

    # Must have joint activities plus at least one age-specific category
    passed = has_joint and (has_younger or has_older)
    # Bonus: ideally all three are present
    all_present = has_joint and has_younger and has_older

    group_counts = {}
    for e in events:
        ag = e.get("age_suitability", "unknown")
        group_counts[ag] = group_counts.get(ag, 0) + 1

    detail_parts = [f"{k}: {v}" for k, v in sorted(group_counts.items())]

    return {
        "name": "age_distribution",
        "passed": passed,
        "score_detail": 1.0 if all_present else (0.7 if passed else 0.0),
        "details": f"Age groups: {', '.join(detail_parts)}. "
                   f"{'All 3 groups represented' if all_present else 'Missing: ' + ', '.join(g for g, present in [('joint', has_joint), ('younger', has_younger), ('older', has_older)] if not present)}",
    }


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


def eval_description_completeness(events: list[dict]) -> dict:
    """Check that events have meaningful 'why_recommended' explanations.

    Flags empty, very short, or generic descriptions.
    """
    if not events:
        return {"name": "description_completeness", "passed": True, "details": "No events"}

    issues = []
    generic_phrases = {"great activity", "fun for kids", "good event", "nice activity", "recommended"}

    for e in events:
        why = e.get("why_recommended", "").strip()
        name = e.get("name", "?")

        if not why:
            issues.append(f"{name}: empty description")
        elif len(why) < 20:
            issues.append(f"{name}: too short ({len(why)} chars)")
        elif why.lower() in generic_phrases:
            issues.append(f"{name}: too generic")

    passed = len(issues) <= len(events) * 0.2  # Allow up to 20% weak descriptions
    return {
        "name": "description_completeness",
        "passed": passed,
        "details": "; ".join(issues) if issues else f"All {len(events)} events have meaningful descriptions",
    }


def eval_url_presence(events: list[dict]) -> dict:
    """Check that events have source URLs for user verification.

    Events without URLs can't be verified by the user.
    """
    if not events:
        return {"name": "url_presence", "passed": True, "details": "No events"}

    missing_url = [e.get("name", "?") for e in events if not e.get("url", "").strip()]
    total = len(events)
    has_url_count = total - len(missing_url)
    ratio = has_url_count / total if total > 0 else 1.0

    passed = ratio >= 0.7  # At least 70% should have URLs
    return {
        "name": "url_presence",
        "passed": passed,
        "details": f"{has_url_count}/{total} events have URLs ({ratio:.0%})"
                   + (f". Missing: {', '.join(missing_url[:3])}" if missing_url else ""),
    }


def run_all_code_evals(state: dict) -> list[dict]:
    """Run all code-based evals on the agent state."""
    categorized = state.get("categorized_output", {})
    events = state.get("ranked_events", [])
    mode = state.get("mode", "outdoor")
    weather = state.get("weather", {})

    results = [
        # --- Structural checks ---
        eval_result_count(categorized),
        eval_radius_compliance(events),
        eval_cost_ordering(categorized),
        eval_rating_threshold(events),
        eval_category_validity(events),
        eval_age_labeling(events),
        eval_weather_consistency(mode, weather),
        eval_no_duplicates(events),
        eval_keyword_relevance(events, mode),
        # --- Quality & coverage checks (new) ---
        eval_age_distribution(events),
        eval_free_event_ratio(events),
        eval_category_diversity(categorized),
        eval_description_completeness(events),
        eval_url_presence(events),
        # --- Confidence / authenticity checks (new) ---
        eval_rating_authenticity(events),
        eval_geocoding_confidence(events),
    ]

    for r in results:
        r["eval_type"] = "code"
        # Use score_detail if provided (for gradient scores), else binary
        r["score"] = r.pop("score_detail", 1.0 if r["passed"] else 0.0)

    return results
