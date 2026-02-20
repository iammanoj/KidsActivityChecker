"""Tavily search wrapper for event discovery."""

import os
from datetime import datetime

from tavily import TavilyClient


def _get_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set")
    return TavilyClient(api_key=api_key)


def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Execute a single Tavily search with error handling."""
    client = _get_client()
    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []


def search_events(
    location_city: str,
    location_state: str,
    mode: str,
    time_mode: str,
    age_group: str,
) -> list[dict]:
    """Search for events using Tavily.

    Args:
        location_city: City name (e.g. "Los Altos")
        location_state: State (e.g. "California")
        mode: "indoor" or "outdoor"
        time_mode: "today" or "weekend"
        age_group: "kids_8", "teens_14", or "family"
    """
    age_desc = {
        "kids_8": "kids ages 6-10 children elementary",
        "teens_14": "teens ages 12-16 teenage",
        "family": "family-friendly all ages kids and teens",
    }.get(age_group, "family-friendly kids")

    time_desc = "today" if time_mode == "today" else "this weekend"
    location = f"{location_city}, {location_state}"

    query = (
        f"Free {mode} activities events for {age_desc} near {location} "
        f"{time_desc} {datetime.now().strftime('%B %Y')} "
        f"girl-friendly collaborative team building"
    )

    return _tavily_search(query, max_results=5)


def search_by_category(
    location_city: str,
    location_state: str,
    mode: str,
    time_mode: str,
    category: str,
) -> list[dict]:
    """Search for events in a specific category to improve diversity.

    This targets underrepresented categories that generic searches miss.
    """
    time_desc = "today" if time_mode == "today" else "this weekend"
    location = f"{location_city}, {location_state}"
    month_year = datetime.now().strftime("%B %Y")

    category_queries = {
        "Sports & Fitness": (
            f"Free {mode} kids sports fitness soccer basketball swimming "
            f"classes clinics near {location} {time_desc} {month_year} girls youth"
        ),
        "Arts & Crafts": (
            f"Free {mode} kids art crafts painting pottery creative workshop "
            f"near {location} {time_desc} {month_year} girls"
        ),
        "Nature & Outdoor": (
            f"Free nature parks hiking trails gardens botanical "
            f"near {location} {time_desc} {month_year} kids family"
        ),
        "Entertainment": (
            f"Free {mode} kids entertainment shows movies theater festivals "
            f"near {location} {time_desc} {month_year} family"
        ),
        "Educational": (
            f"Free {mode} kids educational museum science library STEM coding "
            f"near {location} {time_desc} {month_year} girls teens"
        ),
        "Social & Community": (
            f"Free {mode} kids community events volunteer meetups social "
            f"near {location} {time_desc} {month_year} family girls"
        ),
    }

    query = category_queries.get(category)
    if not query:
        return []

    results = _tavily_search(query, max_results=4)
    for r in results:
        r["_target_category"] = category
    return results


def search_paid_events(
    location_city: str,
    location_state: str,
    mode: str,
    time_mode: str,
) -> list[dict]:
    """Fallback search for paid events when free events are sparse."""
    location = f"{location_city}, {location_state}"
    time_desc = "today" if time_mode == "today" else "this weekend"

    query = (
        f"Best affordable {mode} activities events for kids and teens near {location} "
        f"{time_desc} {datetime.now().strftime('%B %Y')} "
        f"low cost girl-friendly rated well-reviewed Google Yelp rating"
    )

    return _tavily_search(query, max_results=6)
