"""Ranking and parsing node — uses LLM to structure and rank raw search results."""

import json
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agent.state import VALID_CATEGORIES, VALID_AGE_SUITABILITY

SYSTEM_PROMPT = """You are an activity recommendation engine for a family with two girls (ages 8 and 14)
in the San Francisco Bay Area. Your job is to parse raw web search results into structured activity
recommendations.

For each activity, extract or infer:
- name: Activity/event name
- category: One of {categories}
- location_name: Venue name
- address: Street address (best guess from context)
- distance_miles: Estimated distance from {city}, {state} (0-15 miles)
- cost: Dollar amount (0.0 if free)
- is_free: true/false
- rating: Rating out of 5.0 (estimate from context clues if not explicit, use 4.0 as default)
- rating_source: Where the rating comes from (e.g. "Google", "Yelp", "estimated")
- age_suitability: "joint" (good for both 8 & 14), "younger" (better for 8yr), or "older" (better for 14yr)
- why_recommended: 1-2 sentence explanation of why this is a good pick for the family
- url: Source URL

RANKING PRIORITIES (apply these weights):
1. Cost (25%): Free > cheap > expensive
2. Rating (20%): Higher is better. EXCLUDE anything below 3.5/5
3. Age-appropriateness (20%): Must suit target age group
4. Girl-friendly appeal (15%): Activities appealing to girls
5. Social/collaborative (10%): Team activities, meeting other kids
6. Distance (10%): Closer is better

IMPORTANT RULES:
- Only include activities within 15 miles of {city}, {state}
- Exclude anything rated below 3.5 stars
- Prioritize free events; include paid only as fallback
- Focus on activities girls would enjoy
- Prioritize collaborative/social activities
- Return ONLY valid JSON array, no markdown or extra text
"""


def rank_and_parse(state: dict) -> dict:
    """Use Claude to parse raw search results into structured, ranked events."""
    raw_results = state.get("raw_search_results", [])
    location = state["location"]
    mode = state["mode"]

    if not raw_results:
        return {**state, "events": [], "ranked_events": []}

    # Prepare raw results text for the LLM
    results_text = ""
    for i, r in enumerate(raw_results):
        results_text += f"\n--- Result {i+1} ---\n"
        results_text += f"Title: {r.get('title', 'N/A')}\n"
        results_text += f"URL: {r.get('url', 'N/A')}\n"
        results_text += f"Content: {r.get('content', 'N/A')[:500]}\n"
        results_text += f"Age query: {r.get('_age_query', 'family')}\n"

    system = SYSTEM_PROMPT.format(
        categories=", ".join(VALID_CATEGORIES),
        city=location["city"],
        state=location["state"],
    )

    user_msg = f"""Parse these {mode} activity search results for {location['city']}, {location['state']}.
Current mode: {mode.upper()} activities.
Time: {state.get('time_mode', 'today')}.

Raw search results:
{results_text}

Return a JSON array of activity objects, ranked best-to-worst. Include 15-20 activities if possible.
Return ONLY the JSON array, no other text."""

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2,
        max_tokens=4000,
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=user_msg),
        ])

        # Parse JSON from response
        text = response.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        events = json.loads(text)

        # Validate and clean events
        cleaned = []
        for e in events:
            if not isinstance(e, dict):
                continue
            # Enforce valid category
            if e.get("category") not in VALID_CATEGORIES:
                e["category"] = "Entertainment"
            # Enforce valid age_suitability
            if e.get("age_suitability") not in VALID_AGE_SUITABILITY:
                e["age_suitability"] = "joint"
            # Enforce rating threshold
            if e.get("rating", 0) < 3.5:
                continue
            cleaned.append(e)

        return {**state, "events": cleaned, "ranked_events": cleaned}

    except Exception as e:
        return {**state, "events": [], "ranked_events": [], "error": f"Ranking error: {e}"}
