"""Tests for the deterministic season-plan generator (Tier 0 #4)."""
from datetime import date
from app.tools.season_plan import generate_season_plan, _CROPS


def test_every_crop_produces_a_valid_plan():
    for key in _CROPS:
        plan = generate_season_plan(key, area_acres=2, soil_type="loam")
        assert "error" not in plan, key
        assert plan["validation"]["valid"], (key, plan["validation"]["checks"])


def test_required_checkpoints_present_for_every_crop():
    required = ["has_land_prep", "has_sowing", "fertilizer_splits_at_least_2",
               "has_irrigation", "has_pest_checkpoint", "has_harvest"]
    for key in _CROPS:
        checks = generate_season_plan(key)["validation"]["checks"]
        for r in required:
            assert checks[r], (key, r)


def test_stages_are_date_ordered():
    for key in _CROPS:
        stages = generate_season_plan(key)["stages"]
        offsets = [s["day_offset"] for s in stages]
        assert offsets == sorted(offsets), key
        dates = [s["date"] for s in stages]
        assert dates == sorted(dates), key


def test_harvest_equals_start_plus_duration():
    for key, c in _CROPS.items():
        plan = generate_season_plan(key, start_date="2026-11-01")
        start = date.fromisoformat(plan["start_date"])
        harvest = date.fromisoformat(plan["harvest_date"])
        assert (harvest - start).days == c["duration_days"], key


def test_explicit_start_date_is_used():
    plan = generate_season_plan("boro_rice", start_date="2027-01-01")
    assert plan["start_date"] == "2027-01-01"
    assert plan["start_date_source"] == "farmer/agent-provided"


def test_derived_start_date_is_upcoming():
    # with no start_date, day 0 is derived from the sowing window, in the future or today
    plan = generate_season_plan("wheat")
    assert date.fromisoformat(plan["start_date"]) >= date.today()
    assert "derived from sowing window" in plan["start_date_source"]


def test_unknown_crop_returns_error():
    out = generate_season_plan("banana")
    assert "error" in out and "banana" in out["error"]


def test_fertilizer_schedule_has_dates_and_at_least_two():
    plan = generate_season_plan("boro_rice")
    fert = plan["fertilizer_schedule_dates"]
    assert len(fert) >= 2
    for f in fert:
        assert f["date"] and "stage" in f


def test_bad_start_date_format_errors():
    out = generate_season_plan("wheat", start_date="01-11-2026")
    assert "error" in out
