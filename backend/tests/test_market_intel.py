"""Tests for market price intelligence + supplier comparison (Tier 2)."""
from app.tools.market_intel import market_price_intelligence as mpi, _SEAS
from app.tools.suppliers import compare_suppliers as cmp


# ---- market intelligence ----
def test_every_crop_has_intel():
    for key in _SEAS:
        r = mpi(key)
        assert "error" not in r, key
        assert r["recommendation"]["action"] in ("sell_now", "store", "wait")


def test_crop_alias_resolves_to_price_key():
    r = mpi("boro_rice")  # maps to rice_paddy
    assert "error" not in r
    assert r["current_price_bdt_per_kg"] > 0


def test_perishable_tomato_says_sell_now():
    r = mpi("tomato")
    assert r["storage"]["storable"] is False
    assert r["recommendation"]["action"] == "sell_now"


def test_history_has_12_months_and_range():
    r = mpi("potato")
    assert len(r["history_monthly"]) == 12
    m = r["modeled_12_month"]
    assert m["low"] < m["high"]


def test_store_recommendation_beats_current_when_chosen():
    # if the engine says store/wait, the projected net must exceed current price
    for key in _SEAS:
        r = mpi(key)
        rec = r["recommendation"]
        if rec["action"] in ("store", "wait"):
            assert rec["expected_net_bdt_per_kg"] > r["current_price_bdt_per_kg"]


def test_unknown_crop_errors():
    assert "error" in mpi("banana")


# ---- supplier comparison ----
def test_compare_sorts_by_price_cheapest_first():
    r = cmp("urea")
    prices = [s["unit_price_bdt"] for s in r["suppliers"]]
    assert prices == sorted(prices)
    assert r["best_price"]["unit_price_bdt"] == prices[0]


def test_quantity_totals_line_cost():
    r = cmp("urea", quantity=5)
    for s in r["suppliers"]:
        assert s["line_total_bdt"] == round(s["unit_price_bdt"] * 5)


def test_sort_by_delivery_and_rating():
    fast = cmp("urea", sort_by="delivery")
    assert fast["suppliers"][0]["delivery_days"] == min(s["delivery_days"] for s in fast["suppliers"])
    rated = cmp("urea", sort_by="rating")
    assert rated["suppliers"][0]["rating"] == max(s["rating"] for s in rated["suppliers"])


def test_unknown_item_errors():
    assert "error" in cmp("spaceship")
