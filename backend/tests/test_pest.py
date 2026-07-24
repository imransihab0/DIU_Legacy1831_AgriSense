"""Tests for the deterministic pest & disease risk engine (Tier 1)."""
from app.tools.pest import assess_pest_risk as risk, _PESTS


def test_every_crop_has_rules_and_runs():
    for key in _PESTS:
        r = risk(key, growth_stage="vegetative", temp_c=25, recent_rain_mm=15)
        assert "error" not in r, key
        assert "threats" in r and "overall_risk" in r


def test_unknown_crop_errors():
    assert "error" in risk("banana")


def test_potato_late_blight_high_in_cool_wet_weather():
    r = risk("potato", growth_stage="vegetative", temp_c=16, recent_rain_mm=20)
    lb = next(t for t in r["threats"] if "Late blight" in t["name"])
    assert lb["risk_level"] == "high"
    assert r["overall_risk"] == "high"


def test_potato_late_blight_lower_in_hot_dry_weather():
    cool = risk("potato", growth_stage="vegetative", temp_c=16, recent_rain_mm=20)
    hot = risk("potato", growth_stage="vegetative", temp_c=32, recent_rain_mm=0)
    cool_lb = next(t for t in cool["threats"] if "Late blight" in t["name"])["risk_score"]
    hot_lb = next((t for t in hot["threats"] if "Late blight" in t["name"]), None)
    # in hot dry weather late blight is either dropped or scored lower
    assert hot_lb is None or hot_lb["risk_score"] < cool_lb


def test_moisture_signal_from_humidity_and_rain():
    wet = risk("boro_rice", growth_stage="tillering", temp_c=30, humidity_pct=90)
    assert wet["inputs"]["moisture_signal"] == "wet"
    dry = risk("wheat", growth_stage="flowering", temp_c=20, humidity_pct=45)
    assert dry["inputs"]["moisture_signal"] == "dry"


def test_threats_sorted_by_risk():
    r = risk("boro_rice", growth_stage="reproductive", temp_c=30, recent_rain_mm=20)
    order = {"high": 3, "medium": 2, "low": 1}
    scores = [order[t["risk_level"]] for t in r["threats"]]
    assert scores == sorted(scores, reverse=True)


def test_area_scales_total_cost():
    r = risk("potato", growth_stage="vegetative", temp_c=16, recent_rain_mm=20, area_acres=3)
    lb = next(t for t in r["threats"] if "Late blight" in t["name"])
    assert lb["est_treatment_cost_bdt_total"] == lb["est_treatment_cost_bdt_per_acre"] * 3


def test_no_inputs_still_returns_without_crash():
    r = risk("maize")
    assert "threats" in r  # neutral scoring, no weather/stage given
