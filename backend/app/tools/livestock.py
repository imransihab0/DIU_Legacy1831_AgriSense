"""Deterministic livestock engine — finance + rearing/vaccination calendar.

Farming is crops AND animals. This gives livestock the same grounded, costed,
dated treatment crops get:
  - compute_livestock_financials  ->  cost/revenue/net/ROI/break-even per cycle
  - generate_livestock_plan       ->  dated procurement→vaccination→sale calendar

All arithmetic and dates are computed in Python (never the LLM). Baseline numbers
are seeded reference data in livestock.json; vaccination schedules follow standard
DLS/BLRI practice (confirm with a local vet).
"""
import json
from datetime import date, timedelta
from ..config import DATA_DIR

_ANIMALS = json.loads((DATA_DIR / "livestock.json").read_text())["animals"]


def _norm(animal: str) -> str:
    return animal.lower().strip().replace(" ", "_").replace("-", "_")


def list_animals() -> dict:
    return {
        k: {"display": v["display"], "unit": v["unit"], "cycle_days": v["cycle_days"],
            "typical_count": v["typical_count"]}
        for k, v in _ANIMALS.items()
    }


# --------------------------------------------------------------------------- #
# Finance
# --------------------------------------------------------------------------- #
def compute_livestock_financials(
    animal: str,
    count: float | None = None,
    price_override: float | None = None,
    yield_factor: float = 1.0,
    cost_factor: float = 1.0,
    price_factor: float = 1.0,
    mortality_pct: float | None = None,
    budget_bdt: float | None = None,
) -> dict:
    """Cost/revenue/net/ROI/break-even for a livestock batch over one cycle.

    Scenario overrides mirror the crop engine: yield_factor (output per animal),
    cost_factor, price_factor, plus a mortality_pct override.
    """
    key = _norm(animal)
    if key not in _ANIMALS:
        return {"error": f"Unknown animal '{animal}'. Valid keys: {list(_ANIMALS)}"}
    a = _ANIMALS[key]
    n = float(count) if (count and float(count) > 0) else a["typical_count"]
    mort = a["mortality_pct"] if mortality_pct is None else float(mortality_pct)
    survivors = n * (1 - mort / 100)

    items = {name: round(amount * cost_factor * n) for name, amount in a["costs_bdt_per_unit"].items()}
    total_cost = sum(items.values())

    rev = a["revenue"]
    if rev["type"] == "weight":
        price = round((price_override or rev["price_per_kg"]) * price_factor, 2)
        output_kg = round(survivors * rev["sale_weight_kg"] * yield_factor, 1)
        revenue = round(output_kg * price)
        output = {"total_live_weight_kg": output_kg, "price_per_kg_bdt": price,
                  "surviving_animals": round(survivors, 1)}
        breakeven = {"break_even_price_bdt_per_kg": round(total_cost / output_kg, 2) if output_kg else None}
    else:  # product (milk / eggs)
        price = round((price_override or rev["price_per_unit"]) * price_factor, 2)
        per_unit = rev["yield_per_unit"] * yield_factor
        total_product = round(survivors * per_unit)
        salvage = round(survivors * rev.get("salvage_bdt_per_unit", 0))
        revenue = round(total_product * price + salvage)
        output = {f"total_{rev['product']}": total_product, "price_per_unit_bdt": price,
                  "salvage_bdt": salvage, "surviving_animals": round(survivors, 1)}
        breakeven = {"break_even_price_per_unit_bdt": round((total_cost - salvage) / total_product, 2)
                     if total_product else None}

    net_profit = revenue - total_cost
    roi_pct = round(net_profit / total_cost * 100, 1) if total_cost else None

    result = {
        "animal": a["display"],
        "animal_key": key,
        "count": n,
        "cycle_days": a["cycle_days"],
        "assumptions": {
            "mortality_pct": mort,
            "revenue_model": rev["type"],
            "price_source": "farmer-provided" if price_override else "seeded reference (labeled)",
            "yield_factor": yield_factor, "cost_factor": cost_factor, "price_factor": price_factor,
            "note": a.get("note"),
        },
        "cost_breakdown_bdt": items,
        "total_cost_bdt": total_cost,
        "output": output,
        "expected_revenue_bdt": revenue,
        "net_profit_bdt": net_profit,
        "roi_pct": roi_pct,
        **breakeven,
    }
    if budget_bdt is not None:
        result["budget_bdt"] = budget_bdt
        result["within_budget"] = total_cost <= float(budget_bdt)
        result["budget_gap_bdt"] = round(float(budget_bdt) - total_cost)
    return result


# --------------------------------------------------------------------------- #
# Rearing / vaccination calendar
# --------------------------------------------------------------------------- #
# (offset_days_from_start, stage, category, action)
_SCHEDULES = {
    "broiler": [
        (0, "Chick placement & brooding", "procurement", "Place day-old chicks; brood at 32-34°C, start on starter feed."),
        (5, "ND + IB vaccine", "vaccination", "Newcastle Disease + Infectious Bronchitis vaccine (eye/nose drop)."),
        (10, "Gumboro (IBD) vaccine", "vaccination", "Infectious Bursal Disease vaccine in drinking water."),
        (14, "Gumboro booster", "vaccination", "IBD booster dose."),
        (18, "Switch to grower feed", "feed", "Move from starter to grower ration; ensure clean water."),
        (21, "ND booster (Lasota)", "vaccination", "Newcastle booster; weigh a sample of birds."),
        (28, "Finisher feed + weight check", "health_check", "Switch to finisher feed; check average weight vs target."),
        (35, "Marketing", "sale", "Sell at ~1.8 kg live weight; withdraw medicated feed before sale."),
    ],
    "layer": [
        (0, "Chick placement & brooding", "procurement", "Place chicks; brood and start on chick starter."),
        (7, "ND + IB vaccine", "vaccination", "Newcastle + IB vaccine."),
        (14, "Gumboro (IBD) vaccine", "vaccination", "IBD vaccine in water."),
        (21, "ND booster", "vaccination", "Newcastle booster (Lasota)."),
        (35, "Fowl pox vaccine", "vaccination", "Fowl pox wing-web vaccination."),
        (56, "Deworming", "deworming", "Deworm; move to grower ration."),
        (112, "Switch to layer feed", "feed", "At ~16 weeks shift to layer ration with calcium; add nest boxes."),
        (140, "Point of lay", "health_check", "Laying begins (~20 weeks); monitor egg production and shell quality."),
        (365, "End of laying cycle", "sale", "Cull/sell spent hens at end of first laying cycle."),
    ],
    "goat_fattening": [
        (0, "Procurement & quarantine", "procurement", "Buy healthy kids; quarantine and observe 7-10 days before mixing."),
        (3, "Deworming", "deworming", "Deworm against internal parasites."),
        (7, "PPR vaccine", "vaccination", "Peste des Petits Ruminants vaccine."),
        (14, "FMD vaccine", "vaccination", "Foot-and-Mouth Disease vaccine."),
        (30, "Anthrax vaccine (endemic areas)", "vaccination", "Anthrax vaccination where endemic."),
        (90, "Deworming + weight check", "health_check", "Repeat deworming; weigh and adjust concentrate feed."),
        (180, "Marketing", "sale", "Sell at target weight (~18 kg); time to Eid market if possible."),
    ],
    "beef_fattening": [
        (0, "Procurement & quarantine", "procurement", "Buy healthy bulls; quarantine and observe before starting feed."),
        (3, "Deworming", "deworming", "Deworm against internal and external parasites."),
        (7, "FMD vaccine", "vaccination", "Foot-and-Mouth Disease vaccine."),
        (14, "Anthrax + HS + BQ vaccine", "vaccination", "Anthrax, Haemorrhagic Septicaemia and Black Quarter vaccination."),
        (75, "Deworming + weight check", "health_check", "Repeat deworming; weigh and adjust the fattening ration."),
        (150, "Marketing", "sale", "Sell at target weight; aim for the Qurbani/Eid market for best price."),
    ],
    "dairy_cow": [
        (0, "Calving / lactation start", "procurement", "Lactation begins after calving; feed for peak milk yield."),
        (7, "Peak-lactation feeding", "feed", "Maximise concentrate + green fodder for early-lactation yield."),
        (60, "Re-breeding (AI)", "breeding", "Inseminate ~60 days after calving to keep a yearly calving interval."),
        (90, "Deworming", "deworming", "Deworm; check body condition and milk yield trend."),
        (210, "Pregnancy check", "health_check", "Confirm pregnancy; plan the dry-off."),
        (245, "Dry-off preparation", "feed", "Reduce concentrate to begin drying off ~2 months before next calving."),
        (305, "Dry off / end lactation", "sale", "Stop milking; give the cow a 60-day dry period before next calving."),
    ],
}


def generate_livestock_plan(
    animal: str,
    count: float | None = None,
    start_date: str | None = None,
) -> dict:
    """Deterministic, dated, validated rearing + vaccination calendar for one animal."""
    key = _norm(animal)
    if key not in _ANIMALS:
        return {"error": f"Unknown animal '{animal}'. Valid keys: {list(_ANIMALS)}"}
    a = _ANIMALS[key]
    cycle = int(a["cycle_days"])

    if start_date:
        try:
            day0 = date.fromisoformat(start_date)
        except ValueError:
            return {"error": f"start_date must be YYYY-MM-DD, got '{start_date}'"}
        start_source = "farmer/agent-provided"
    else:
        day0 = date.today()
        start_source = "defaulted to today"

    stages = [
        {"day_offset": off, "date": (day0 + timedelta(days=off)).isoformat(),
         "stage": name, "category": cat, "action": act}
        for off, name, cat, act in _SCHEDULES[key]
    ]
    stages.sort(key=lambda s: s["day_offset"])
    end_date = (day0 + timedelta(days=cycle)).isoformat()

    cats = [s["category"] for s in stages]
    checks = {
        "dates_in_order": all(stages[i]["day_offset"] <= stages[i + 1]["day_offset"]
                              for i in range(len(stages) - 1)),
        "has_procurement_start": "procurement" in cats,
        "has_vaccination_or_health": any(c in cats for c in ("vaccination", "deworming", "health_check", "breeding")),
        "has_sale_or_end": "sale" in cats,
        "cycle_within_last_stage": stages[-1]["day_offset"] <= cycle,
    }

    vaccinations = [{"date": s["date"], "day_offset": s["day_offset"], "stage": s["stage"], "action": s["action"]}
                    for s in stages if s["category"] in ("vaccination", "deworming")]

    return {
        "animal": a["display"],
        "animal_key": key,
        "count": float(count) if count else a["typical_count"],
        "unit": a["unit"],
        "start_date": day0.isoformat(),
        "start_date_source": start_source,
        "cycle_days": cycle,
        "cycle_end_date": end_date,
        "stages": stages,
        "vaccination_deworming_schedule": vaccinations,
        "validation": {"valid": all(checks.values()), "checks": checks},
        "grounding": (
            "Dates computed deterministically from the animal's cycle length + a standard "
            "DLS/BLRI rearing & vaccination schedule. Vaccination timing is indicative — confirm "
            "exact products/dates with a local vet or DLS office."
        ),
    }
