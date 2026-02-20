"""Tavily search wrapper for event discovery."""

import os
from datetime import datetime

from tavily import TavilyClient


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
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set")

    client = TavilyClient(api_key=api_key)

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

    try:
        response = client.search(
            query=query,
            max_results=8,
            search_depth="advanced",
            include_answer=True,
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []


def search_paid_events(
    location_city: str,
    location_state: str,
    mode: str,
    time_mode: str,
) -> list[dict]:
    """Fallback search for paid events when free events are sparse."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set")

    client = TavilyClient(api_key=api_key)
    location = f"{location_city}, {location_state}"
    time_desc = "today" if time_mode == "today" else "this weekend"

    query = (
        f"Best affordable {mode} activities events for kids and teens near {location} "
        f"{time_desc} {datetime.now().strftime('%B %Y')} "
        f"low cost girl-friendly rated well-reviewed"
    )

    try:
        response = client.search(
            query=query,
            max_results=6,
            search_depth="advanced",
            include_answer=True,
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Tavily paid search error: {e}")
        return []
