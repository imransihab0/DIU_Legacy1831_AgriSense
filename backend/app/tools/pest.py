"""Deterministic pest & disease risk engine (Tier 1).

Scores likely pests/diseases for a crop from the LIVE weather (temperature +
moisture) and the crop's current growth stage, using seeded rules in pests.json
(same public IPM sources as kb/pest_management.md). Returns a risk level per threat
with prevention, treatment and an indicative per-acre cost — so pest advice is
grounded in weather+stage, not model recall.
"""
import json
from ..config import DATA_DIR

_PESTS = json.loads((DATA_DIR / "pests.json").read_text())["crops"]

_LEVELS = [(2.25, "high"), (1.5, "medium"), (0.75, "low")]


def _norm(crop: str) -> str:
    return crop.lower().strip().replace(" ", "_")


def _moisture_signal(humidity_pct, recent_rain_mm) -> str | None:
    """Classify current moisture as 'wet', 'dry', or None (unknown)."""
    if humidity_pct is not None:
        if humidity_pct >= 80:
            return "wet"
        if humidity_pct <= 55:
            return "dry"
    if recent_rain_mm is not None:
        if recent_rain_mm >= 10:
            return "wet"
        if recent_rain_mm < 3:
            return "dry"
    return None


def _temp_score(temp_c, lo, hi) -> float:
    if temp_c is None:
        return 0.5
    if lo <= temp_c <= hi:
        return 1.0
    if lo - 3 <= temp_c <= hi + 3:
        return 0.5
    return 0.0


def _stage_score(growth_stage, stages) -> float:
    if not growth_stage:
        return 0.5
    g = growth_stage.lower()
    return 1.0 if any(s in g for s in stages) else 0.0


def _moist_score(signal, wants) -> float:
    if wants == "any":
        return 0.5
    if signal is None:
        return 0.5
    return 1.0 if signal == wants else 0.0


def _level(score: float) -> str | None:
    for cutoff, name in _LEVELS:
        if score >= cutoff:
            return name
    return None


def assess_pest_risk(
    crop: str,
    growth_stage: str | None = None,
    temp_c: float | None = None,
    humidity_pct: float | None = None,
    recent_rain_mm: float | None = None,
    area_acres: float | None = None,
) -> dict:
    """Return weather+stage-driven pest/disease risk for a crop.

    Feed temp_c and recent_rain_mm (or humidity_pct) from the live forecast, and
    growth_stage from the season plan (e.g. 'vegetative', 'flowering', 'tuber bulking').
    """
    key = _norm(crop)
    if key not in _PESTS:
        return {"error": f"No pest rules for crop '{crop}'. Valid keys: {list(_PESTS)}"}

    signal = _moisture_signal(humidity_pct, recent_rain_mm)
    threats = []
    for t in _PESTS[key]:
        score = (
            _temp_score(temp_c, t["temp_c"][0], t["temp_c"][1])
            + _moist_score(signal, t["moisture"])
            + _stage_score(growth_stage, t["stages"])
        )
        level = _level(score)
        if not level:
            continue
        cost = t["treatment_cost_bdt_per_acre"]
        threats.append({
            "name": t["name"],
            "type": t["type"],
            "risk_level": level,
            "risk_score": round(score, 2),
            "favoured_by": {"temp_c": t["temp_c"], "moisture": t["moisture"], "stages": t["stages"]},
            "symptoms": t["symptoms"],
            "prevention": t["prevention"],
            "treatment": t["treatment"],
            "suggested_product": t["product"],
            "est_treatment_cost_bdt_per_acre": cost,
            "est_treatment_cost_bdt_total": round(cost * area_acres) if area_acres else None,
        })

    order = {"high": 3, "medium": 2, "low": 1}
    threats.sort(key=lambda x: (order[x["risk_level"]], x["risk_score"]), reverse=True)
    overall = threats[0]["risk_level"] if threats else "low"

    return {
        "crop": key,
        "inputs": {
            "growth_stage": growth_stage, "temp_c": temp_c,
            "humidity_pct": humidity_pct, "recent_rain_mm": recent_rain_mm,
            "moisture_signal": signal, "area_acres": area_acres,
        },
        "overall_risk": overall,
        "threats": threats,
        "grounding": (
            "Risk scored deterministically from live temperature + moisture and the crop's "
            "growth stage against seeded IPM rules (pests.json / kb/pest_management.md). Costs "
            "are indicative per-acre estimates — confirm products/doses with DAE and follow IPM "
            "(resistant variety → sanitation → mechanical → biological → chemical last)."
        ),
    }
