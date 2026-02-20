"""Reusable Streamlit UI components."""

import streamlit as st


def weather_card(weather: dict, mode: str):
    """Display weather summary card."""
    emoji = "☀️" if mode == "outdoor" else "🌧️"
    mode_color = "green" if mode == "outdoor" else "blue"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {'#667eea' if mode == 'indoor' else '#f093fb'} 0%, {'#764ba2' if mode == 'indoor' else '#f5576c'} 100%);
                padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h2 style="margin:0">{emoji} {weather.get('temp_f', 'N/A')}°F — {weather.get('description', 'N/A').title()}</h2>
        <p style="margin:5px 0 0 0; font-size:1.1em">
            Mode: <strong>{mode.upper()}</strong> activities
            | Wind: {weather.get('wind_mph', 'N/A')} mph
            | Humidity: {weather.get('humidity', 'N/A')}%
        </p>
    </div>
    """, unsafe_allow_html=True)


def activity_card(event: dict, activity_db_id: int | None, session_id: int | None):
    """Display a single activity card with feedback buttons."""
    cost_str = "FREE" if event.get("is_free") else f"${event.get('cost', 0):.2f}"
    cost_color = "#28a745" if event.get("is_free") else "#dc3545"

    age_emoji = {"joint": "👨‍👩‍👧‍👧", "younger": "👧", "older": "👩"}.get(
        event.get("age_suitability", "joint"), "👨‍👩‍👧‍👧"
    )
    age_label = {"joint": "Both (8 & 14)", "younger": "Age 8", "older": "Age 14"}.get(
        event.get("age_suitability", "joint"), "All"
    )

    rating = event.get("rating", 0)
    stars = "★" * int(rating) + "☆" * (5 - int(rating))

    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 10px;
                    background: white;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h4 style="margin:0; color:#333">{event.get('name', 'Unknown Activity')}</h4>
                <span style="color:{cost_color}; font-weight:bold; font-size:1.1em">{cost_str}</span>
            </div>
            <p style="margin:5px 0; color:#666; font-size:0.9em">
                📍 {event.get('location_name', 'N/A')} ({event.get('distance_miles', '?')} mi)
                &nbsp;|&nbsp; {stars} {rating}/5
                &nbsp;|&nbsp; {age_emoji} {age_label}
            </p>
            <p style="margin:5px 0; color:#555; font-style:italic">
                "{event.get('why_recommended', 'N/A')}"
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Feedback buttons
        if activity_db_id and session_id:
            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                if st.button("👍", key=f"up_{activity_db_id}"):
                    from db.database import save_feedback
                    save_feedback(activity_db_id, session_id, "up")
                    st.toast("Thanks for the feedback!")
            with col2:
                if st.button("👎", key=f"down_{activity_db_id}"):
                    from db.database import save_feedback
                    save_feedback(activity_db_id, session_id, "down")
                    st.toast("Thanks for the feedback!")
            with col3:
                url = event.get("url", "")
                if url:
                    st.markdown(f"[🔗 Details]({url})")


def eval_summary_sidebar(eval_results: dict):
    """Display eval summary in sidebar."""
    if not eval_results:
        st.sidebar.info("No eval results yet")
        return

    code_evals = eval_results.get("code_evals", {})
    llm_judge = eval_results.get("llm_judge", {})

    st.sidebar.markdown("### 📊 Eval Scores")

    # Code evals
    pass_rate = code_evals.get("pass_rate", 0)
    color = "green" if pass_rate >= 90 else "orange" if pass_rate >= 70 else "red"
    st.sidebar.markdown(
        f"**Code Evals:** <span style='color:{color}'>{code_evals.get('passed', 0)}/"
        f"{code_evals.get('total', 0)} ({pass_rate}%)</span>",
        unsafe_allow_html=True,
    )

    # LLM judge
    judge_score = llm_judge.get("score", 0)
    judge_color = "green" if judge_score >= 3.5 else "orange" if judge_score >= 2.5 else "red"
    st.sidebar.markdown(
        f"**LLM Judge:** <span style='color:{judge_color}'>{judge_score:.1f}/5</span>",
        unsafe_allow_html=True,
    )
