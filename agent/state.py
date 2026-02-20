"""Agent state schema for the LangGraph workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


@dataclass
class Event:
    """A single activity/event recommendation."""

    name: str
    category: str
    location_name: str
    address: str
    distance_miles: float
    cost: float
    is_free: bool
    rating: float
    rating_source: str
    age_suitability: str  # "joint" | "younger" | "older"
    why_recommended: str
    url: str
    source_query: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "location_name": self.location_name,
            "address": self.address,
            "distance_miles": self.distance_miles,
            "cost": self.cost,
            "is_free": self.is_free,
            "rating": self.rating,
            "rating_source": self.rating_source,
            "age_suitability": self.age_suitability,
            "why_recommended": self.why_recommended,
            "url": self.url,
            "source_query": self.source_query,
        }


VALID_CATEGORIES = [
    "Educational",
    "Sports & Fitness",
    "Arts & Crafts",
    "Social & Community",
    "Nature & Outdoor",
    "Entertainment",
]

VALID_AGE_SUITABILITY = ["joint", "younger", "older"]


class AgentState(TypedDict, total=False):
    """State that flows through the LangGraph workflow."""

    location: dict  # {city, state, lat, lon}
    weather: dict  # {temp_f, condition, description, is_outdoor}
    mode: str  # "indoor" | "outdoor"
    time_mode: str  # "today" | "weekend"
    raw_search_results: list[dict]
    events: list[dict]  # parsed Event dicts
    ranked_events: list[dict]
    categorized_output: dict[str, list[dict]]  # category -> events
    eval_results: dict
    error: str
