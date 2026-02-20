"""Weather check node."""

from agent.tools.weather_tool import get_weather


def check_weather(state: dict) -> dict:
    """Fetch weather and determine indoor/outdoor mode."""
    location = state["location"]

    try:
        weather = get_weather(location["lat"], location["lon"])
        mode = "outdoor" if weather["is_outdoor"] else "indoor"
        return {**state, "weather": weather, "mode": mode}
    except Exception as e:
        return {
            **state,
            "weather": {
                "temp_f": 70.0,
                "condition": "Unknown",
                "description": "weather unavailable",
                "is_outdoor": True,
            },
            "mode": "outdoor",
            "error": f"Weather API error: {e}",
        }
