"""Weather API wrapper — OpenWeatherMap with Open-Meteo fallback."""

import os

import requests

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OUTDOOR_TEMP_THRESHOLD_F = 65.0
RAIN_CODES = set(range(200, 622))  # thunderstorm, drizzle, rain, snow
# WMO weather codes that indicate precipitation
WMO_RAIN_CODES = {
    51, 53, 55, 56, 57,  # drizzle
    61, 63, 65, 66, 67,  # rain
    71, 73, 75, 77,      # snow
    80, 81, 82,           # rain showers
    85, 86,               # snow showers
    95, 96, 99,           # thunderstorm
}


def get_weather(lat: float, lon: float) -> dict:
    """Fetch current weather for coordinates.

    Tries OpenWeatherMap first, falls back to Open-Meteo (free, no key needed).
    Returns dict with temp_f, condition, description, is_outdoor.
    """
    try:
        return _get_weather_owm(lat, lon)
    except Exception:
        return _get_weather_open_meteo(lat, lon)


def _get_weather_owm(lat: float, lon: float) -> dict:
    """Primary: OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY not set")

    resp = requests.get(
        OPENWEATHERMAP_URL,
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "imperial"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    temp_f = data["main"]["temp"]
    weather_id = data["weather"][0]["id"]
    condition = data["weather"][0]["main"]
    description = data["weather"][0]["description"]

    is_rainy = weather_id in RAIN_CODES
    is_outdoor = temp_f >= OUTDOOR_TEMP_THRESHOLD_F and not is_rainy

    return {
        "temp_f": round(temp_f, 1),
        "condition": condition,
        "description": description,
        "weather_id": weather_id,
        "is_outdoor": is_outdoor,
        "humidity": data["main"].get("humidity"),
        "wind_mph": round(data["wind"].get("speed", 0), 1),
    }


def _get_weather_open_meteo(lat: float, lon: float) -> dict:
    """Fallback: Open-Meteo API (free, no API key required)."""
    resp = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    current = data["current"]
    temp_f = current["temperature_2m"]
    wmo_code = current["weather_code"]
    humidity = current["relative_humidity_2m"]
    wind_mph = current["wind_speed_10m"]

    is_rainy = wmo_code in WMO_RAIN_CODES
    is_outdoor = temp_f >= OUTDOOR_TEMP_THRESHOLD_F and not is_rainy

    # Map WMO codes to human-readable conditions
    if wmo_code == 0:
        condition, description = "Clear", "clear sky"
    elif wmo_code in (1, 2, 3):
        condition, description = "Clouds", "partly cloudy"
    elif wmo_code in (45, 48):
        condition, description = "Fog", "foggy"
    elif wmo_code in WMO_RAIN_CODES:
        condition, description = "Rain", "rainy"
    else:
        condition, description = "Clear", "fair weather"

    return {
        "temp_f": round(temp_f, 1),
        "condition": condition,
        "description": description,
        "weather_id": wmo_code,
        "is_outdoor": is_outdoor,
        "humidity": humidity,
        "wind_mph": round(wind_mph, 1),
    }
