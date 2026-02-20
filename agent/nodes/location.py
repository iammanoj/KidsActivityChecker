"""Location detection node."""

import requests

DEFAULT_LOCATION = {
    "city": "Los Altos",
    "state": "California",
    "lat": 37.3685,
    "lon": -122.0977,
}


def detect_location(state: dict) -> dict:
    """Detect user location via IP geolocation, fallback to Los Altos."""
    # If location already provided (manual override), use it
    if state.get("location") and state["location"].get("lat"):
        return state

    try:
        resp = requests.get("http://ip-api.com/json/", timeout=5)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "success":
            return {
                **state,
                "location": {
                    "city": data.get("city", DEFAULT_LOCATION["city"]),
                    "state": data.get("regionName", DEFAULT_LOCATION["state"]),
                    "lat": data.get("lat", DEFAULT_LOCATION["lat"]),
                    "lon": data.get("lon", DEFAULT_LOCATION["lon"]),
                },
            }
    except Exception:
        pass

    return {**state, "location": DEFAULT_LOCATION}
