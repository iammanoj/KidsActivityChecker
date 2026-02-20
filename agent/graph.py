"""LangGraph workflow definition for the Kids Activity Tracker."""

from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes.location import detect_location
from agent.nodes.weather import check_weather
from agent.nodes.search import search_activities
from agent.nodes.rank import rank_and_parse
from agent.nodes.explain import categorize_events


def build_graph() -> StateGraph:
    """Build and compile the activity tracker workflow graph.

    Flow: detect_location -> check_weather -> search_activities
          -> rank_and_parse -> categorize_events -> END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("detect_location", detect_location)
    graph.add_node("check_weather", check_weather)
    graph.add_node("search_activities", search_activities)
    graph.add_node("rank_and_parse", rank_and_parse)
    graph.add_node("categorize_events", categorize_events)

    # Define edges (linear pipeline)
    graph.set_entry_point("detect_location")
    graph.add_edge("detect_location", "check_weather")
    graph.add_edge("check_weather", "search_activities")
    graph.add_edge("search_activities", "rank_and_parse")
    graph.add_edge("rank_and_parse", "categorize_events")
    graph.add_edge("categorize_events", END)

    return graph.compile()


def run_activity_tracker(
    time_mode: str = "today",
    location_override: dict | None = None,
) -> dict:
    """Run the full activity tracker pipeline.

    Args:
        time_mode: "today" or "weekend"
        location_override: Optional {city, state, lat, lon} to override auto-detection

    Returns:
        Final agent state with categorized_output, eval_results, etc.
    """
    graph = build_graph()

    initial_state: AgentState = {
        "time_mode": time_mode,
    }
    if location_override:
        initial_state["location"] = location_override

    result = graph.invoke(initial_state)
    return result
