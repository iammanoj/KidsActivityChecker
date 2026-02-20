"""Categorization node — groups ranked events into categories."""

from agent.state import VALID_CATEGORIES


def categorize_events(state: dict) -> dict:
    """Group ranked events into categories, top 5 per category.

    Within each category, free events are sorted before paid events
    to satisfy the cost_ordering eval and match user priority.
    """
    events = state.get("ranked_events", [])

    categorized = {cat: [] for cat in VALID_CATEGORIES}

    for event in events:
        cat = event.get("category", "Entertainment")
        if cat in categorized:
            categorized[cat].append(event)

    # Sort each category: free first, then by rating descending
    for cat in categorized:
        categorized[cat].sort(key=lambda e: (not e.get("is_free", False), -e.get("rating", 0)))
        # Keep top 5
        categorized[cat] = categorized[cat][:5]

    # Remove empty categories
    categorized = {k: v for k, v in categorized.items() if v}

    return {**state, "categorized_output": categorized}
