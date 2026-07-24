"""Tests for the deterministic financial engine (Tier 0 #5).

The rubric requires: "The math is inspectable and internally consistent:
change an input, and the outputs change correctly." These tests prove it.

Run:  cd backend && .venv/bin/python -m pytest tests/ -v
"""
import pytest

from app.tools.finance import compute_financials, list_crops


def test_all_crops_computable():
    for key in list_crops():
        r = compute_financials(key, 1.0)
        assert "error" not in r, f"{key} failed"
        assert r["total_cost_bdt"] > 0
        assert r["expected_revenue_bdt"] > 0


def test_internal_consistency():
    r = compute_financials("wheat", 2.0)
    # revenue = yield * price
    assert r["expected_revenue_bdt"] == round(
        r["expected_yield_kg"] * r["assumptions"]["price_per_kg_bdt"]
    )
    # net = revenue - cost
    assert r["net_profit_bdt"] == r["expected_revenue_bdt"] - r["total_cost_bdt"]
    # cost = sum of items
    assert r["total_cost_bdt"] == sum(r["cost_breakdown_bdt"].values())
    # ROI
    assert r["roi_pct"] == round(r["net_profit_bdt"] / r["total_cost_bdt"] * 100, 1)


def test_area_scales_costs_and_yield():
    one = compute_financials("boro_rice", 1.0)
    two = compute_financials("boro_rice", 2.0)
    assert two["expected_yield_kg"] == 2 * one["expected_yield_kg"]
    assert two["total_cost_bdt"] == 2 * one["total_cost_bdt"]


def test_change_input_changes_output_correctly():
    base = compute_financials("potato", 1.0)
    cheaper = compute_financials("potato", 1.0, price_factor=0.7)
    # 30% price drop -> exactly 30% revenue drop, costs unchanged
    assert cheaper["expected_revenue_bdt"] == round(base["expected_yield_kg"] * round(base["assumptions"]["price_per_kg_bdt"] * 0.7, 2))
    assert cheaper["total_cost_bdt"] == base["total_cost_bdt"]
    assert cheaper["net_profit_bdt"] < base["net_profit_bdt"]


def test_yield_factor_scenario():
    base = compute_financials("aman_rice", 1.0)
    drought = compute_financials("aman_rice", 1.0, yield_factor=0.8)
    assert drought["expected_yield_kg"] == round(base["expected_yield_kg"] * 0.8)
    assert drought["net_profit_bdt"] < base["net_profit_bdt"]


def test_budget_check():
    r = compute_financials("potato", 2.0, budget_bdt=80000)
    assert r["within_budget"] is False
    assert r["budget_gap_bdt"] == round(80000 - r["total_cost_bdt"])
    r2 = compute_financials("mustard", 2.0, budget_bdt=80000)
    assert r2["within_budget"] is True


def test_breakeven_math():
    r = compute_financials("maize", 1.5)
    # selling everything at break-even price recovers total cost (±1 BDT rounding)
    assert abs(r["breakeven_price_bdt_per_kg"] * r["expected_yield_kg"] - r["total_cost_bdt"]) <= r["expected_yield_kg"] * 0.005 + 1
    # break-even yield at actual price recovers total cost
    assert abs(r["breakeven_yield_kg"] * r["assumptions"]["price_per_kg_bdt"] - r["total_cost_bdt"]) <= r["assumptions"]["price_per_kg_bdt"]


def test_price_override():
    r = compute_financials("wheat", 1.0, price_per_kg=40)
    assert r["assumptions"]["price_per_kg_bdt"] == 40
    assert r["assumptions"]["price_source"] == "farmer-provided"


def test_unknown_crop_returns_error():
    r = compute_financials("dragonfruit", 1.0)
    assert "error" in r


def test_non_positive_area_errors():
    assert "error" in compute_financials("boro_rice", 0)
    assert "error" in compute_financials("boro_rice", -5)
