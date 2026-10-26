"""Live weather via Open-Meteo (no API key). Failures surface as clear API errors."""
from __future__ import annotations

import httpx

from .errors import AppError
from .schemas import WeatherDay, WeatherNow

GEO = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"


async def fetch_weather(location: str) -> tuple[str, WeatherNow, list[WeatherDay]]:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            g = await client.get(GEO, params={"name": location, "count": 1, "language": "en"})
            g.raise_for_status()
            results = g.json().get("results") or []
            if not results:
                raise AppError("location_not_found", f"No location found for '{location}'. Try a nearby city name.", 404)
            p = results[0]
            f = await client.get(FORECAST, params={
                "latitude": p["latitude"], "longitude": p["longitude"], "timezone": "auto", "forecast_days": 5,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            })
            f.raise_for_status()
            data = f.json()
    except AppError:
        raise
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise AppError("weather_unavailable", "Live weather data could not be retrieved. Check the connection and try again.", 502) from exc

    try:
        cur = data["current"]
        now = WeatherNow(temperature_c=cur["temperature_2m"], humidity_pct=cur["relative_humidity_2m"],
                         wind_kph=cur["wind_speed_10m"], precipitation_mm=cur["precipitation"])
        d = data["daily"]
        days = [WeatherDay(date=d["time"][i], temp_max_c=d["temperature_2m_max"][i], temp_min_c=d["temperature_2m_min"][i],
                           precipitation_mm=d["precipitation_sum"][i] or 0, wind_max_kph=d["wind_speed_10m_max"][i])
                for i in range(len(d["time"]))]
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError("weather_unavailable", "Weather provider returned unexpected data.", 502) from exc
    label = ", ".join(x for x in [p.get("name"), p.get("admin1"), p.get("country")] if x)
    return label, now, days
