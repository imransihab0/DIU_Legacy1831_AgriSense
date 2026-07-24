"""Proactive weather-triggered alerts (Tier 1).

Watches the LIVE forecast against the farm's persisted season plan and raises
alerts WITHOUT waiting for a chat turn: the frontend polls /api/alerts and the
agent can also call check_weather_alerts. Deterministic — thresholds in Python.

Core rule (from the brief's example): heavy rain near a scheduled nitrogen
application or sowing date -> advise delaying it to cut runoff loss.
"""
from datetime import date, datetime, timedelta
from .. import db
from . import weather

HEAVY_RAIN_MM = 25.0      # summed over the sensitivity window around a stage
GENERAL_RAIN_MM = 40.0    # a single-day downpour worth a standalone heads-up
DRY_DAY_MM = 5.0          # a day dry enough to reschedule an application to

# stage categories whose timing is sensitive to heavy rain
_N_SENSITIVE = {"fertilizer", "sowing", "land_prep"}


def _rain_by_date(forecast: dict) -> dict:
    return {d["date"]: d.get("rain_mm", 0) for d in forecast.get("daily", [])}


def _window_rain(rain: dict, d: date, lo=-1, hi=2) -> float:
    return sum(rain.get((d + timedelta(days=k)).isoformat(), 0) for k in range(lo, hi + 1))


def _next_dry_day(rain: dict, d: date, horizon_end: date) -> date | None:
    probe = d + timedelta(days=1)
    while probe <= horizon_end:
        if rain.get(probe.isoformat(), 0) <= DRY_DAY_MM and _window_rain(rain, probe, 0, 1) <= HEAVY_RAIN_MM:
            return probe
        probe += timedelta(days=1)
    return None


def compute_weather_alerts(plan: dict, forecast: dict, today: date | None = None) -> list[dict]:
    """Return alerts for upcoming plan stages that clash with the live forecast."""
    today = today or date.today()
    rain = _rain_by_date(forecast)
    if not rain:
        return []
    horizon_end = max(date.fromisoformat(x) for x in rain)
    alerts = []

    for s in plan.get("stages", []):
        try:
            sd = date.fromisoformat(s["date"])
        except (ValueError, KeyError):
            continue
        if sd < today or sd > horizon_end:
            continue  # only alert on stages inside the live forecast window
        wet = _window_rain(rain, sd)
        cat = s.get("category")
        if cat in _N_SENSITIVE and wet >= HEAVY_RAIN_MM:
            dry = _next_dry_day(rain, sd, horizon_end)
            delay = (dry - sd).days if dry else None
            sug = (f"Delay it ~{delay} day(s) to {dry.isoformat()} (drier) to cut runoff/leaching loss."
                   if dry else "Hold the application until the rain passes to cut runoff loss.")
            alerts.append({
                "severity": "high",
                "date": s["date"],
                "stage": s.get("stage"),
                "message": f"Heavy rain (~{round(wet)} mm) around {s['date']}, near '{s.get('stage')}'.",
                "suggestion": sug,
            })
        elif cat == "irrigation" and wet >= HEAVY_RAIN_MM:
            alerts.append({
                "severity": "info",
                "date": s["date"],
                "stage": s.get("stage"),
                "message": f"Rain (~{round(wet)} mm) around your irrigation date {s['date']}.",
                "suggestion": "You can likely skip this irrigation — the rain covers it. Save the water/fuel cost.",
            })
        elif cat == "pest" and wet >= HEAVY_RAIN_MM:
            alerts.append({
                "severity": "medium",
                "date": s["date"],
                "stage": s.get("stage"),
                "message": f"Rain (~{round(wet)} mm) around the pest-scouting date {s['date']}.",
                "suggestion": "Wet, humid weather raises fungal disease risk — scout early and time any spray to a dry spell.",
            })

    # standalone downpour heads-up (fires even without a plan hit)
    for d in forecast.get("daily", []):
        try:
            dd = date.fromisoformat(d["date"])
        except (ValueError, KeyError):
            continue
        if today <= dd <= today + timedelta(days=5) and d.get("rain_mm", 0) >= GENERAL_RAIN_MM:
            alerts.append({
                "severity": "medium",
                "date": d["date"],
                "stage": None,
                "message": f"Heavy rain (~{round(d['rain_mm'])} mm) forecast on {d['date']}.",
                "suggestion": "Avoid fertilizer/spray just before it; ensure field drainage.",
            })

    alerts.sort(key=lambda a: a["date"])
    return alerts


def get_session_alerts(session_id: str) -> dict:
    """Load the farm's plan + location, fetch live weather, and compute alerts.

    This is the non-chat 'proactive' path: called by the /api/alerts poll and the
    agent's check_weather_alerts tool.
    """
    plan = db.get_plan(session_id)
    profile = db.get_profile(session_id)
    if not plan:
        return {"status": "no_active_plan", "alerts": [],
                "note": "No season plan saved yet — create one with generate_season_plan first."}
    location = profile.get("location")
    if not location:
        return {"status": "no_location", "alerts": [], "crop": plan.get("crop"),
                "note": "Farm location unknown — cannot fetch weather."}
    geo = weather.geocode_location(location)
    if "error" in geo or geo.get("latitude") is None:
        return {"status": "geocode_failed", "alerts": [], "crop": plan.get("crop")}
    forecast = weather.get_weather_forecast(geo["latitude"], geo["longitude"], days=14)
    alerts = compute_weather_alerts(plan, forecast, date.today())
    return {
        "status": "ok",
        "crop": plan.get("crop"),
        "location": location,
        "weather_source": forecast.get("source"),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "alert_count": len(alerts),
        "alerts": alerts,
    }


def check_weather_alerts(session_id: str) -> dict:
    """Agent tool wrapper — proactively check the saved plan against the live forecast."""
    return get_session_alerts(session_id)
