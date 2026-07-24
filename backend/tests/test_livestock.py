"""Tests for the deterministic livestock engine (finance + rearing calendar)."""
from datetime import date
from app.tools.livestock import (
    compute_livestock_financials as fin,
    generate_livestock_plan as plan,
    _ANIMALS,
)


# ---- finance ----
def test_all_animals_computable():
    for key in _ANIMALS:
        r = fin(key)
        assert "error" not in r, key
        for f in ("total_cost_bdt", "expected_revenue_bdt", "net_profit_bdt", "roi_pct"):
            assert f in r, (key, f)


def test_costs_and_revenue_scale_with_count():
    one = fin("broiler", count=100)
    two = fin("broiler", count=200)
    assert two["total_cost_bdt"] == 2 * one["total_cost_bdt"]
    assert two["expected_revenue_bdt"] == 2 * one["expected_revenue_bdt"]


def test_net_profit_is_revenue_minus_cost():
    for key in _ANIMALS:
        r = fin(key)
        assert r["net_profit_bdt"] == r["expected_revenue_bdt"] - r["total_cost_bdt"]


def test_higher_mortality_lowers_revenue():
    base = fin("broiler", count=100, mortality_pct=5)
    worse = fin("broiler", count=100, mortality_pct=25)
    assert worse["expected_revenue_bdt"] < base["expected_revenue_bdt"]


def test_price_factor_scales_revenue_for_weight_animal():
    base = fin("goat_fattening")
    up = fin("goat_fattening", price_factor=1.2)
    assert up["expected_revenue_bdt"] > base["expected_revenue_bdt"]


def test_product_animal_has_product_output():
    r = fin("dairy_cow")
    assert r["assumptions"]["revenue_model"] == "product"
    assert any("milk" in k for k in r["output"])


def test_budget_check():
    r = fin("beef_fattening", count=2, budget_bdt=100000)
    assert "within_budget" in r and "budget_gap_bdt" in r


def test_unknown_animal_errors():
    assert "error" in fin("elephant")


# ---- rearing / vaccination calendar ----
def test_every_animal_plan_valid():
    for key in _ANIMALS:
        p = plan(key)
        assert "error" not in p, key
        assert p["validation"]["valid"], (key, p["validation"]["checks"])


def test_plan_has_vaccination_schedule():
    for key in _ANIMALS:
        p = plan(key)
        # every animal should surface at least one vaccination/deworming event
        assert len(p["vaccination_deworming_schedule"]) >= 1, key


def test_plan_dates_ordered_and_start_used():
    p = plan("broiler", start_date="2026-08-01")
    offs = [s["day_offset"] for s in p["stages"]]
    assert offs == sorted(offs)
    assert p["start_date"] == "2026-08-01"
    assert date.fromisoformat(p["cycle_end_date"]) > date.fromisoformat(p["start_date"])


def test_plan_unknown_animal_errors():
    assert "error" in plan("dragon")


def test_non_positive_count_falls_back_to_typical():
    typical = fin("broiler")["count"]
    assert fin("broiler", count=0)["count"] == typical
    assert fin("broiler", count=-3)["count"] == typical
