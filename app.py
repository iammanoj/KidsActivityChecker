"""Kids Activity Tracker — Streamlit entry point."""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from db.database import init_db, save_session, save_activities
from agent.graph import build_graph
from agent.state import AgentState
from evals.run_evals import run_all_evals
from ui.components import weather_card, eval_summary_sidebar
from ui.dashboard import render_results_tab, render_eval_tab

# Initialize DB on first run
init_db()

# Pipeline steps with display labels and progress weights
PIPELINE_STEPS = [
    ("detect_location", "Detecting location...", 0.05),
    ("check_weather", "Checking weather...", 0.10),
    ("search_activities", "Searching activities (7 parallel queries)...", 0.55),
    ("rank_and_parse", "AI ranking & structuring results...", 0.80),
    ("categorize_events", "Categorizing events...", 0.95),
]
STEP_LABELS = {name: (label, weight) for name, label, weight in PIPELINE_STEPS}

st.set_page_config(
    page_title="Kids Activity Tracker",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Kids Activity Tracker")
st.caption("AI-powered activity recommendations for your family")

# --- Sidebar ---
st.sidebar.header("Settings")

# Location override
use_auto_location = st.sidebar.checkbox("Auto-detect location", value=True)
location_override = None
if not use_auto_location:
    city = st.sidebar.text_input("City", value="Los Altos")
    state = st.sidebar.text_input("State", value="California")
    lat = st.sidebar.number_input("Latitude", value=37.3685, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=-122.0977, format="%.4f")
    location_override = {"city": city, "state": state, "lat": lat, "lon": lon}

# Time mode
time_mode = st.sidebar.radio("Time Frame", ["today", "weekend"], index=0)

# Age filter
st.sidebar.markdown("**Age Filter**")
show_joint = st.sidebar.checkbox("Joint (both kids)", value=True)
show_younger = st.sidebar.checkbox("Age 8", value=True)
show_older = st.sidebar.checkbox("Age 14", value=True)

age_filter = []
if show_joint:
    age_filter.append("joint")
if show_younger:
    age_filter.append("younger")
if show_older:
    age_filter.append("older")
st.session_state["age_filter"] = age_filter

# Cost filter
cost_filter = st.sidebar.radio("Cost Filter", ["all", "free"], index=0)
st.session_state["cost_filter"] = cost_filter

st.sidebar.divider()

# --- Run Button ---
run_clicked = st.sidebar.button("🔄 Find Activities", type="primary", use_container_width=True)

# --- Main Content ---
if run_clicked:
    # Build initial state
    initial_state: AgentState = {"time_mode": time_mode}
    if location_override:
        initial_state["location"] = location_override

    # Stream through the graph with live progress
    graph = build_graph()
    progress_bar = st.progress(0, text="Starting pipeline...")
    result = initial_state

    for step_output in graph.stream(initial_state):
        # step_output is {node_name: state_update}
        node_name = list(step_output.keys())[0]
        result = step_output[node_name]

        if node_name in STEP_LABELS:
            label, weight = STEP_LABELS[node_name]
            progress_bar.progress(weight, text=f"✅ {label.replace('...', ' — done!')}")

    progress_bar.progress(0.97, text="📊 Running evaluations...")

    # Store in session state
    st.session_state["result"] = result

    # Display weather
    if result.get("weather"):
        weather_card(result["weather"], result.get("mode", "outdoor"))
        st.markdown(
            f"📍 **{result['location'].get('city', 'N/A')}, "
            f"{result['location'].get('state', 'N/A')}** | "
            f"Mode: **{result.get('mode', 'N/A').upper()}** | "
            f"Time: **{time_mode.title()}**"
        )

    # Save to DB
    session_id = save_session(
        result.get("location", {}),
        result.get("weather", {}),
        result.get("mode", "outdoor"),
        time_mode,
    )
    st.session_state["session_id"] = session_id

    # Save activities
    all_events = result.get("ranked_events", [])
    activity_ids = save_activities(session_id, all_events)
    st.session_state["activity_ids"] = activity_ids

    # Run evals
    eval_results = run_all_evals(result, session_id)
    st.session_state["eval_results"] = eval_results

    progress_bar.progress(1.0, text="✅ All done!")

    # Show eval summary in sidebar
    eval_summary_sidebar(eval_results)

    # Tabs
    tab1, tab2 = st.tabs(["📋 Activities", "📊 Eval Results"])

    with tab1:
        render_results_tab(result, session_id, activity_ids)

    with tab2:
        render_eval_tab(eval_results)

elif "result" in st.session_state:
    # Re-render from session state (page refresh)
    result = st.session_state["result"]
    session_id = st.session_state.get("session_id")
    activity_ids = st.session_state.get("activity_ids", [])
    eval_results = st.session_state.get("eval_results", {})

    if result.get("weather"):
        weather_card(result["weather"], result.get("mode", "outdoor"))
        st.markdown(
            f"📍 **{result['location'].get('city', 'N/A')}, "
            f"{result['location'].get('state', 'N/A')}** | "
            f"Mode: **{result.get('mode', 'N/A').upper()}** | "
            f"Time: **{result.get('time_mode', 'today').title()}**"
        )

    eval_summary_sidebar(eval_results)

    tab1, tab2 = st.tabs(["📋 Activities", "📊 Eval Results"])
    with tab1:
        render_results_tab(result, session_id, activity_ids)
    with tab2:
        render_eval_tab(eval_results)
else:
    st.info("👈 Click **Find Activities** in the sidebar to get started!")
    st.markdown("""
    ### How it works
    1. **Weather Check** — Detects your location and checks current weather
    2. **Smart Search** — Searches for indoor/outdoor activities within 15 miles
    3. **AI Ranking** — Ranks activities by cost, rating, age-fit, and more
    4. **Categorized Results** — Groups activities into 6 categories
    5. **Quality Evals** — Runs code-based + LLM judge evaluations
    """)
