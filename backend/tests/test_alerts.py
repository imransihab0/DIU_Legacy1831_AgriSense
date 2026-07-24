"""Tests for the proactive weather-alert engine (Tier 1)."""
from datetime import date, timedelta
from app.tools.alerts import compute_weather_alerts


def _forecast(rain_by_offset, base):
    """Build a forecast dict; rain_by_offset maps day-offset -> rain_mm."""
    return {"source": "test", "daily": [
        {"date": (base + timedelta(days=k)).isoformat(),
         "t_max_c": 30, "t_min_c": 22, "rain_mm": rain_by_offset.get(k, 0)}
        for k in range(0, 14)
    ]}


def _plan_with_stage(category, offset, base):
    d = (base + timedelta(days=offset)).isoformat()
    return {"crop": "Test", "stages": [
        {"day_offset": offset, "date": d, "stage": "Urea top-dress", "category": category}
    ]}


def test_heavy_rain_near_fertilizer_raises_high_alert():
    base = date(2026, 8, 1)
    plan = _plan_with_stage("fertilizer", 3, base)
    fc = _forecast({3: 30}, base)  # 30mm on the fertilizer day
    alerts = compute_weather_alerts(plan, fc, today=base)
    assert any(a["severity"] == "high" for a in alerts)


def test_no_alert_when_dry_around_fertilizer():
    base = date(2026, 8, 1)
    plan = _plan_with_stage("fertilizer", 3, base)
    fc = _forecast({3: 2}, base)
    alerts = compute_weather_alerts(plan, fc, today=base)
    assert not any(a["stage"] == "Urea top-dress" for a in alerts)


def test_suggestion_points_to_a_drier_day():
    base = date(2026, 8, 1)
    plan = _plan_with_stage("fertilizer", 2, base)
    fc = _forecast({2: 40, 3: 30, 4: 0, 5: 0}, base)  # wet then clears
    alerts = compute_weather_alerts(plan, fc, today=base)
    high = [a for a in alerts if a["severity"] == "high"][0]
    assert "day" in high["suggestion"].lower() or "hold" in high["suggestion"].lower()


def test_irrigation_rain_gives_skip_advice():
    base = date(2026, 8, 1)
    plan = _plan_with_stage("irrigation", 4, base)
    fc = _forecast({4: 35}, base)
    alerts = compute_weather_alerts(plan, fc, today=base)
    assert any("skip" in a["suggestion"].lower() for a in alerts)


def test_past_and_beyond_horizon_stages_are_ignored():
    base = date(2026, 8, 1)
    plan = {"crop": "T", "stages": [
        {"date": (base - timedelta(days=2)).isoformat(), "stage": "past", "category": "fertilizer"},
        {"date": (base + timedelta(days=40)).isoformat(), "stage": "far", "category": "fertilizer"},
    ]}
    fc = _forecast({0: 50}, base)
    alerts = compute_weather_alerts(plan, fc, today=base)
    assert not any(a["stage"] in ("past", "far") for a in alerts)


def test_standalone_downpour_heads_up():
    base = date(2026, 8, 1)
    plan = {"crop": "T", "stages": []}
    fc = _forecast({2: 55}, base)
    alerts = compute_weather_alerts(plan, fc, today=base)
    assert any("Heavy rain" in a["message"] for a in alerts)
