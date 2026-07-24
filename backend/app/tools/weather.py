"""Live weather grounding via Open-Meteo (free, no API key).

Tier 0 requirement #2: the agent must call a REAL weather API and use the
actual returned values. Nothing here is mocked.

Resilience: every successful live response is cached to disk. If the network
fails mid-demo, the last real response is served, explicitly labeled
"CACHED", so the agent degrades gracefully instead of erroring.
"""
import json
import time

import httpx

from ..config import DATA_DIR

_CACHE_FILE = DATA_DIR / "weather_cache.json"


def _cache_get(key: str):
    try:
        return json.loads(_CACHE_FILE.read_text()).get(key)
    except Exception:
        return None


def _cache_put(key: str, value: dict):
    try:
        cache = json.loads(_CACHE_FILE.read_text())
    except Exception:
        cache = {}
    cache[key] = value
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False))

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Geocoding DBs often use pre-2018 spellings of renamed BD districts
_BD_ALIASES = {
    "bogura": "Bogra",
    "cumilla": "Comilla",
    "chattogram": "Chittagong",
    "barishal": "Barisal",
    "jashore": "Jessore",
}
_STRIP_WORDS = {"district", "division", "upazila", "zila", "sadar", "bangladesh"}


def geocode_location(location_name: str) -> dict:
    # Open-Meteo matches on the place name only — try progressively simpler forms
    cache_key = f"geo:{location_name.lower().strip()}"
    cleaned = location_name.split(",")[0].strip()
    cleaned = " ".join(w for w in cleaned.split() if w.lower() not in _STRIP_WORDS) or cleaned
    candidates = [cleaned]
    alias = _BD_ALIASES.get(cleaned.lower())
    if alias:
        candidates.insert(0, alias)
    if location_name.strip() not in candidates:
        candidates.append(location_name.strip())
    results = []
    try:
        for name in candidates:
            r = httpx.get(
                GEOCODE_URL,
                params={"name": name, "count": 10, "language": "en", "format": "json"},
                timeout=15,
            )
            r.raise_for_status()
            results.extend(r.json().get("results") or [])
    except Exception as e:
        cached = _cache_get(cache_key)
        if cached:
            return {**cached, "source": f"CACHED earlier live geocode (network unavailable: {type(e).__name__})"}
        raise
    if not results:
        return {"error": f"No match found for '{location_name}'. Ask the farmer for a nearby town or district name."}
    # Prefer a Bangladesh match when the farmer's place name is ambiguous globally
    top = next((x for x in results if x.get("country_code") == "BD"), results[0])
    result = {
        "matched_name": top.get("name"),
        "admin1": top.get("admin1"),
        "country": top.get("country"),
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
        "source": "open-meteo geocoding API (live)",
    }
    _cache_put(cache_key, result)
    return result


def get_weather_forecast(latitude: float, longitude: float, days: int = 14) -> dict:
    days = max(1, min(int(days), 16))
    cache_key = f"wx:{round(float(latitude), 2)},{round(float(longitude), 2)}:{days}"
    try:
        r = httpx.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=15,
        )
        r.raise_for_status()
    except Exception as e:
        cached = _cache_get(cache_key)
        if cached:
            return {**cached, "source": f"CACHED earlier live forecast (network unavailable: {type(e).__name__})"}
        raise
    d = r.json().get("daily", {})
    daily = [
        {
            "date": d["time"][i],
            "t_max_c": d["temperature_2m_max"][i],
            "t_min_c": d["temperature_2m_min"][i],
            "rain_mm": d["precipitation_sum"][i],
            "rain_prob_pct": (d.get("precipitation_probability_max") or [None] * days)[i],
        }
        for i in range(len(d.get("time", [])))
    ]
    total_rain = round(sum(x["rain_mm"] or 0 for x in daily), 1)
    result = {
        "days": len(daily),
        "total_rain_mm": total_rain,
        "avg_t_max_c": round(sum(x["t_max_c"] for x in daily) / len(daily), 1) if daily else None,
        "avg_t_min_c": round(sum(x["t_min_c"] for x in daily) / len(daily), 1) if daily else None,
        "daily": daily,
        "source": "open-meteo forecast API (live)",
    }
    _cache_put(cache_key, result)
    return result
