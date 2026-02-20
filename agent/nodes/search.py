"""Event search node — uses Tavily to find activities."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from agent.tools.search_tool import search_events, search_by_category, search_paid_events


def _search_age_group(location_city, location_state, mode, time_mode, age_group):
    """Search for a single age group (runs in thread pool)."""
    results = search_events(
        location_city=location_city,
        location_state=location_state,
        mode=mode,
        time_mode=time_mode,
        age_group=age_group,
    )
    for r in results:
        r["_age_query"] = age_group
    return results


def _search_category(location_city, location_state, mode, time_mode, category):
    """Search for a single category (runs in thread pool)."""
    results = search_by_category(
        location_city=location_city,
        location_state=location_state,
        mode=mode,
        time_mode=time_mode,
        category=category,
    )
    for r in results:
        r["_age_query"] = "family"
    return results


def search_activities(state: dict) -> dict:
    """Search for activities across age groups and categories.

    All 7 searches (3 age groups + 4 categories) run in parallel
    via ThreadPoolExecutor for ~4x speedup.

    Strategy:
    1. Search by age group (family, kids_8, teens_14) for broad coverage
    2. Search by underrepresented categories for diversity
    3. Fall back to paid events if results are sparse
    """
    location = state["location"]
    mode = state["mode"]
    time_mode = state.get("time_mode", "today")
    city, st_ = location["city"], location["state"]

    all_results = []

    # Phase 1 + 2: Run all 7 searches in parallel
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = []

        # 3 age-group searches
        for age_group in ["family", "kids_8", "teens_14"]:
            futures.append(
                executor.submit(_search_age_group, city, st_, mode, time_mode, age_group)
            )

        # 4 category-targeted searches
        for category in ["Sports & Fitness", "Arts & Crafts", "Nature & Outdoor", "Entertainment"]:
            futures.append(
                executor.submit(_search_category, city, st_, mode, time_mode, category)
            )

        for future in as_completed(futures):
            all_results.extend(future.result())

    # Phase 3: If we still have fewer than 5 results, search for paid events
    if len(all_results) < 5:
        paid = search_paid_events(
            location_city=city,
            location_state=st_,
            mode=mode,
            time_mode=time_mode,
        )
        for r in paid:
            r["_age_query"] = "family"
            r["_is_paid_fallback"] = True
        all_results.extend(paid)

    return {**state, "raw_search_results": all_results}
