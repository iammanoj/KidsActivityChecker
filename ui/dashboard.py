"""Main Streamlit dashboard layout."""

import streamlit as st

from .components import weather_card, activity_card, eval_summary_sidebar


def render_results_tab(state: dict, session_id: int, activity_ids: list[int]):
    """Render the activity results tab."""
    categorized = state.get("categorized_output", {})
    if not categorized:
        st.warning("No activities found. Try adjusting your search or check back later.")
        return

    # Age filter from session state
    age_filter = st.session_state.get("age_filter", ["joint", "younger", "older"])
    cost_filter = st.session_state.get("cost_filter", "all")

    # Flatten for ID mapping
    flat_events = []
    for events in categorized.values():
        flat_events.extend(events)

    id_idx = 0  # Track position in activity_ids

    for cat, events in categorized.items():
        filtered = []
        for e in events:
            if e.get("age_suitability") not in age_filter:
                continue
            if cost_filter == "free" and not e.get("is_free"):
                continue
            filtered.append(e)

        if not filtered:
            continue

        st.markdown(f"### {cat}")
        for e in filtered:
            # Map to DB id
            db_id = None
            if id_idx < len(activity_ids):
                db_id = activity_ids[id_idx]
            activity_card(e, db_id, session_id)
            id_idx += 1


def render_eval_tab(eval_results: dict):
    """Render the eval results tab."""
    if not eval_results:
        st.info("Run the tracker to see eval results.")
        return

    # Code evals
    st.markdown("### Code-Based Evals")
    code_evals = eval_results.get("code_evals", {})
    results = code_evals.get("results", [])

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        with st.expander(f"{icon} {r['name']}"):
            st.write(f"**Passed:** {r['passed']}")
            st.write(f"**Details:** {r['details']}")

    st.markdown(
        f"**Overall: {code_evals.get('passed', 0)}/{code_evals.get('total', 0)} "
        f"({code_evals.get('pass_rate', 0)}%)**"
    )

    st.divider()

    # LLM Judge
    st.markdown("### LLM Judge (GPT-4o)")
    llm_judge = eval_results.get("llm_judge", {})
    breakdown = llm_judge.get("breakdown", {})

    if breakdown:
        row1 = st.columns(3)
        row2 = st.columns(3)
        criteria = [
            "relevance", "age_appropriateness", "diversity",
            "girl_friendly_appeal", "social_collaborative", "description_quality",
        ]
        labels = [
            "Relevance", "Age Fit", "Diversity",
            "Girl-Friendly", "Social/Collab", "Descriptions",
        ]
        all_cols = row1 + row2

        for col, criterion, label in zip(all_cols, criteria, labels):
            data = breakdown.get(criterion, {})
            score = data.get("score", 0) if isinstance(data, dict) else 0
            reasoning = data.get("reasoning", "") if isinstance(data, dict) else ""
            with col:
                st.metric(label, f"{score}/5", help=reasoning)

        st.markdown(f"**Overall Score: {llm_judge.get('score', 0):.1f}/5**")
        summary = breakdown.get("summary", "")
        if summary:
            st.info(summary)
    else:
        st.write(f"Score: {llm_judge.get('score', 0)}/5")
        st.write(f"Details: {llm_judge.get('details', 'N/A')}")

    st.divider()

    # Human feedback
    st.markdown("### Human Feedback")
    from db.database import get_feedback_stats
    stats = get_feedback_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("👍 Thumbs Up", stats["thumbs_up"])
    col2.metric("👎 Thumbs Down", stats["thumbs_down"])
    col3.metric("Approval Rate", f"{stats['approval_rate']}%")
