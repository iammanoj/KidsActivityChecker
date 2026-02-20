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
- category: MUST be one of: {categories}
- location_name: Venue name
- address: Street address (best guess from context)
- distance_miles: Estimated distance from {city}, {state} (use realistic non-round numbers like 3.7, 8.2, 11.4)
- cost: Dollar amount (0.0 if free)
- is_free: true/false
- rating: Rating out of 5.0
- rating_source: CRITICAL — use the ACTUAL source of the rating (e.g. "Google", "Yelp", "TripAdvisor").
  If the search result text mentions a specific star rating or review count, extract it and note the source.
  If NO rating is mentioned in the text at all, set rating_source to "estimated" and use a conservative 3.8.
  Do NOT default everything to 4.0 — vary your estimates based on the content quality signals.
- age_suitability: "joint" (good for both 8 & 14), "younger" (better for 8yr old), or "older" (better for 14yr old)
- why_recommended: 1-2 sentence explanation mentioning specific details (age range, group size, what makes it special)
- url: Source URL from the search result

CATEGORY DISTRIBUTION REQUIREMENT:
You MUST spread activities across at least 4 of the 6 categories. Do NOT put everything in "Educational".
Use the _target_category hint when available to assign the correct category.

AGE DISTRIBUTION REQUIREMENT:
You MUST include activities for ALL THREE age groups:
- At least 2-3 activities tagged "younger" (specifically fun for the 8-year-old)
- At least 2-3 activities tagged "older" (specifically engaging for the 14-year-old)
- The rest can be "joint" (enjoyable for both together)

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
    """Use LLM to parse raw search results into structured, ranked events."""
    raw_results = state.get("raw_search_results", [])
    location = state["location"]
    mode = state["mode"]

    if not raw_results:
        return {**state, "events": [], "ranked_events": []}

    # Deduplicate by URL before sending to LLM
    seen_urls = set()
    unique_results = []
    for r in raw_results:
        url = r.get("url", "")
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        unique_results.append(r)

    # Prepare raw results text for the LLM
    results_text = ""
    for i, r in enumerate(unique_results):
        results_text += f"\n--- Result {i+1} ---\n"
        results_text += f"Title: {r.get('title', 'N/A')}\n"
        results_text += f"URL: {r.get('url', 'N/A')}\n"
        results_text += f"Content: {r.get('content', 'N/A')[:500]}\n"
        results_text += f"Age query: {r.get('_age_query', 'family')}\n"
        if r.get("_target_category"):
            results_text += f"Target category: {r['_target_category']}\n"

    system = SYSTEM_PROMPT.format(
        categories=", ".join(VALID_CATEGORIES),
        city=location["city"],
        state=location["state"],
    )

    user_msg = f"""Parse these {mode} activity search results for {location['city']}, {location['state']}.
Current mode: {mode.upper()} activities.
Time: {state.get('time_mode', 'today')}.

REMEMBER:
- Spread across 4+ categories (not just Educational)
- Include younger (8yr), older (14yr), and joint activities
- Extract REAL ratings from the text when available; only use "estimated" when no rating data exists
- Use realistic non-round distances (3.7, not 5.0)

Raw search results:
{results_text}

Return a JSON array of activity objects, ranked best-to-worst. Include 15-25 activities if possible.
Return ONLY the JSON array, no other text."""

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=6000,
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
