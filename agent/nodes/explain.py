"""Categorization node — groups ranked events into categories."""

from agent.state import VALID_CATEGORIES


def categorize_events(state: dict) -> dict:
    """Group ranked events into categories, top 5 per category."""
    events = state.get("ranked_events", [])

    categorized = {cat: [] for cat in VALID_CATEGORIES}

    for event in events:
        cat = event.get("category", "Entertainment")
        if cat in categorized and len(categorized[cat]) < 5:
            categorized[cat].append(event)

    # Remove empty categories
    categorized = {k: v for k, v in categorized.items() if v}

    return {**state, "categorized_output": categorized}
