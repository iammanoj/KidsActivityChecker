"""Event search node — uses Tavily to find activities."""

from agent.tools.search_tool import search_events, search_by_category, search_paid_events


def search_activities(state: dict) -> dict:
    """Search for activities across age groups and categories.

    Strategy:
    1. Search by age group (family, kids_8, teens_14) for broad coverage
    2. Search by underrepresented categories for diversity
    3. Fall back to paid events if results are sparse
    """
    location = state["location"]
    mode = state["mode"]
    time_mode = state.get("time_mode", "today")

    all_results = []

    # Phase 1: Search by age group
    for age_group in ["family", "kids_8", "teens_14"]:
        results = search_events(
            location_city=location["city"],
            location_state=location["state"],
            mode=mode,
            time_mode=time_mode,
            age_group=age_group,
        )
        for r in results:
            r["_age_query"] = age_group
        all_results.extend(results)

    # Phase 2: Category-targeted searches for diversity
    # Search for categories that generic queries often miss
    diversity_categories = ["Sports & Fitness", "Arts & Crafts", "Nature & Outdoor", "Entertainment"]
    for category in diversity_categories:
        results = search_by_category(
            location_city=location["city"],
            location_state=location["state"],
            mode=mode,
            time_mode=time_mode,
            category=category,
        )
        for r in results:
            r["_age_query"] = "family"
        all_results.extend(results)

    # Phase 3: If we still have fewer than 5 results, search for paid events
    if len(all_results) < 5:
        paid = search_paid_events(
            location_city=location["city"],
            location_state=location["state"],
            mode=mode,
            time_mode=time_mode,
        )
        for r in paid:
            r["_age_query"] = "family"
            r["_is_paid_fallback"] = True
        all_results.extend(paid)

    return {**state, "raw_search_results": all_results}
