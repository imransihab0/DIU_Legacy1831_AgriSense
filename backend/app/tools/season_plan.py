"""Deterministic season-plan generator (Tier 0 #4).

Produces a DATED, validated crop calendar from land preparation to harvest —
computed in Python from crops.json (duration, sowing window) plus per-crop-type
agronomic stage schedules, NOT improvised by the LLM. This makes the calendar
inspectable and internally consistent: the dates always order correctly and every
required checkpoint (land prep, sowing, fertilizer splits, irrigation, weed/pest,
harvest) is present and validated.

Fertilizer DOSES still come from the KB (FRG) via search_knowledge_base; this tool
owns the TIMING/date backbone. The agent layers doses + live-forecast adjustments
on top of these dates.
"""
import json
import re
from datetime import date, timedelta
from ..config import DATA_DIR

_CROPS = json.loads((DATA_DIR / "crops.json").read_text())["crops"]

# crop key -> stage-schedule template name
_PLAN_TYPE = {
    "boro_rice": "transplanted_rice",
    "aman_rice": "transplanted_rice",
    "wheat": "cereal",
    "maize": "cereal",
    "potato": "tuber",
    "mustard": "oilseed_pulse",
    "lentil": "oilseed_pulse",
    "onion": "transplanted_veg",
    "tomato": "transplanted_veg",
    "jute": "fiber",
}

# Each stage: (offset, stage_name, category, action, is_fertilizer)
# offset relative to day 0 = sowing (direct) or transplanting (transplanted):
#   int   -> absolute day offset (negative = before day 0, e.g. nursery/land prep)
#   float in (0,1) -> fraction of the crop's duration
#   ("end", n) -> duration - n days
_TEMPLATES = {
    "transplanted_rice": [
        (-30, "Seedbed & nursery sowing", "nursery", "Prepare seedbed and sow nursery; raise seedlings 25-30 days.", False),
        (-2, "Final land prep + basal fertilizer", "land_prep", "2-3 ploughings + puddling; apply ALL TSP/MoP/gypsum/zinc + ~1/3 of urea as basal.", True),
        (0, "Transplanting", "sowing", "Transplant 25-30 day seedlings, 2-3 per hill, ~20x15 cm.", False),
        (6, "Establishment water", "irrigation", "Maintain 2-3 cm standing water for seedling establishment.", False),
        (15, "1st weeding + 1st urea top-dress", "fertilizer", "First weeding; apply 1st urea top-dressing at early tillering.", True),
        (0.27, "2nd urea top-dress", "fertilizer", "2nd urea top-dressing at active/max tillering; keep 3-5 cm water.", True),
        (0.42, "Panicle-stage urea (long-duration only)", "fertilizer", "Final urea at panicle initiation for late-duration varieties.", True),
        (0.45, "Pest & disease scouting", "pest", "Scout stem borer, BPH, leaf folder and blast; spray only above threshold.", False),
        (("end", 12), "Drain field", "irrigation", "Stop irrigation / drain ~12 days before harvest.", False),
        (("end", 0), "Harvest", "harvest", "Harvest at 80-85% golden-grain maturity.", False),
    ],
    "cereal": [
        (-7, "Land preparation + basal fertilizer", "land_prep", "2-3 ploughings; apply all P/K/S/Zn + 1/3 urea as basal at final prep.", True),
        (0, "Sowing", "sowing", "Sow at recommended seed rate and row spacing into moist, well-tilled soil.", False),
        (18, "1st irrigation (CRI) + 1st urea top-dress", "fertilizer", "Crown-root/early irrigation with 1st urea top-dressing.", True),
        (0.20, "Weeding", "weed", "Remove weeds during early vegetative growth to cut nutrient competition.", False),
        (0.35, "2nd irrigation + 2nd urea top-dress", "fertilizer", "Second irrigation with final urea split at active growth.", True),
        (0.50, "Pest & disease checkpoint", "pest", "Scout for stem borer/aphid and leaf blight; treat above threshold.", False),
        (0.65, "Grain-fill irrigation", "irrigation", "Critical irrigation at flowering/grain-fill to protect yield.", False),
        (("end", 0), "Harvest", "harvest", "Harvest at physiological maturity when grain moisture is right.", False),
    ],
    "tuber": [
        (-10, "Land prep + basal fertilizer", "land_prep", "Fine tilth; apply all P/K/S/Zn/B + part of urea as basal (potato needs heavy basal).", True),
        (0, "Planting", "sowing", "Plant sprouted seed tubers on ridges at recommended spacing.", False),
        (25, "Earthing-up + top-dress + irrigation", "fertilizer", "Earth-up, apply remaining urea, give a light irrigation.", True),
        (30, "Late-blight watch begins", "pest", "Begin scouting for late blight; preventive spray if cool, humid, cloudy weather.", False),
        (0.55, "Mid-season irrigation", "irrigation", "Light irrigation at tuber bulking; avoid waterlogging.", False),
        (("end", 10), "Stop irrigation / dehaulming", "irrigation", "Stop irrigation and cut haulms ~10 days before harvest to set skin.", False),
        (("end", 0), "Harvest", "harvest", "Harvest in dry weather once skins are set; cure before storage.", False),
    ],
    "oilseed_pulse": [
        (-7, "Land prep + basal fertilizer", "land_prep", "Prepare fine seedbed; apply all P/K/S + basal N at final prep.", True),
        (0, "Sowing", "sowing", "Broadcast/line-sow into residual moisture at recommended seed rate.", False),
        (18, "Thinning + weeding + light irrigation", "fertilizer", "Thin to spacing, weed, apply any top-dress N, light irrigation if dry.", True),
        (0.40, "Pest & disease checkpoint", "pest", "Scout aphids (mustard) / stemphylium blight (lentil); treat above threshold.", False),
        (0.55, "Flowering irrigation (if dry)", "irrigation", "One irrigation at flowering/pod-fill if soil moisture is low.", False),
        (("end", 0), "Harvest", "harvest", "Harvest when pods/siliqua turn brown; avoid shattering losses.", False),
    ],
    "transplanted_veg": [
        (-25, "Nursery sowing", "nursery", "Raise seedlings in a protected nursery for ~25-30 days.", False),
        (-3, "Land prep + basal fertilizer", "land_prep", "Prepare beds; apply all P/K/S + organic manure + part urea as basal.", True),
        (0, "Transplanting", "sowing", "Transplant healthy seedlings at recommended spacing in the evening.", False),
        (15, "Establishment irrigation + 1st top-dress", "fertilizer", "Light irrigation; 1st urea top-dressing after establishment.", True),
        (35, "2nd top-dress + staking/weeding", "fertilizer", "2nd urea split; stake (tomato) and weed.", True),
        (0.40, "Pest & disease checkpoint", "pest", "Scout thrips/fruit borer/early blight & virus; rogue infected plants.", False),
        (0.60, "Bulking/fruiting irrigation", "irrigation", "Regular light irrigation through bulb/fruit development.", False),
        (("end", 0), "First harvest", "harvest", "Begin harvest at maturity; pick repeatedly for fruiting types.", False),
    ],
    "fiber": [
        (-7, "Land prep + basal fertilizer", "land_prep", "Prepare fine seedbed; apply P/K/S + basal N at final prep.", True),
        (0, "Sowing", "sowing", "Broadcast/line-sow with the pre-monsoon moisture.", False),
        (20, "Thinning + weeding + top-dress", "fertilizer", "Thin to spacing, weed, apply top-dress urea.", True),
        (0.30, "Irrigation if dry spell", "irrigation", "Give a light irrigation if the pre-monsoon dry spell persists during early growth.", False),
        (0.40, "Pest checkpoint", "pest", "Scout for jute hairy caterpillar / semilooper; treat above threshold.", False),
        (("end", 5), "Retting preparation", "harvest", "Harvest at 50% flowering onward; steep bundles in clean water for retting.", False),
        (("end", 0), "Harvest & extraction", "harvest", "Complete harvest and extract fibre after retting.", False),
    ],
}

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def _norm(crop: str) -> str:
    return crop.lower().strip().replace(" ", "_")


def _parse_window_start(window: str, today: date) -> date:
    """First 'Mon DD' in the sowing window, resolved to the next upcoming occurrence."""
    m = re.search(r"([A-Z][a-z]{2})\s+(\d{1,2})", window or "")
    if not m:
        return today
    month, day = _MONTHS.get(m.group(1)), int(m.group(2))
    if not month:
        return today
    cand = date(today.year, month, day)
    if cand < today:
        cand = date(today.year + 1, month, day)
    return cand


def _resolve_offset(offset, duration: int) -> int:
    if isinstance(offset, tuple) and offset[0] == "end":
        return duration - int(offset[1])
    if isinstance(offset, float) and 0 < offset < 1:
        return round(offset * duration)
    return int(offset)


def generate_season_plan(
    crop: str,
    start_date: str | None = None,
    area_acres: float | None = None,
    soil_type: str | None = None,
) -> dict:
    """Return a deterministic, dated, validated season calendar for one crop.

    start_date = the sowing (direct crops) or transplanting (transplanted crops)
    day, ISO 'YYYY-MM-DD'. If omitted, derived from the crop's sowing window as the
    next upcoming occurrence from today.
    """
    key = _norm(crop)
    if key not in _CROPS:
        return {"error": f"Unknown crop '{crop}'. Valid keys: {list(_CROPS)}"}
    c = _CROPS[key]
    duration = int(c["duration_days"])
    today = date.today()

    if start_date:
        try:
            day0 = date.fromisoformat(start_date)
        except ValueError:
            return {"error": f"start_date must be YYYY-MM-DD, got '{start_date}'"}
        start_source = "farmer/agent-provided"
    else:
        day0 = _parse_window_start(c["sowing_window"], today)
        start_source = f"derived from sowing window '{c['sowing_window']}' (next upcoming)"

    stages = []
    for offset, name, category, action, is_fert in _TEMPLATES[_PLAN_TYPE[key]]:
        d = _resolve_offset(offset, duration)
        stages.append({
            "day_offset": d,
            "date": (day0 + timedelta(days=d)).isoformat(),
            "stage": name,
            "category": category,
            "action": action,
            "needs_fertilizer_dose": is_fert,
        })
    stages.sort(key=lambda s: s["day_offset"])

    harvest_date = (day0 + timedelta(days=duration)).isoformat()
    fert_schedule = [
        {"date": s["date"], "day_offset": s["day_offset"], "stage": s["stage"], "action": s["action"]}
        for s in stages if s["needs_fertilizer_dose"]
    ]

    # ---- validation: prove the calendar is internally consistent ----
    cats = [s["category"] for s in stages]
    checks = {
        "dates_in_order": all(
            stages[i]["day_offset"] <= stages[i + 1]["day_offset"] for i in range(len(stages) - 1)
        ),
        "has_land_prep": "land_prep" in cats,
        "has_sowing": "sowing" in cats,
        # count fertilizer APPLICATION events (basal is folded into land_prep), not just the category
        "fertilizer_splits_at_least_2": sum(s["needs_fertilizer_dose"] for s in stages) >= 2,
        "has_irrigation": "irrigation" in cats,
        "has_pest_checkpoint": "pest" in cats,
        "has_harvest": "harvest" in cats,
        "harvest_matches_duration": stages[-1]["date"] == harvest_date,
    }

    return {
        "crop": c["display"],
        "crop_key": key,
        "plan_type": _PLAN_TYPE[key],
        "area_acres": area_acres,
        "soil_type": soil_type,
        "season": c["season"],
        "sowing_window_reference": c["sowing_window"],
        "start_date": day0.isoformat(),
        "start_date_source": start_source,
        "duration_days": duration,
        "harvest_date": harvest_date,
        "stages": stages,
        "fertilizer_schedule_dates": fert_schedule,
        "validation": {"valid": all(checks.values()), "checks": checks},
        "grounding": (
            "Dates computed deterministically from crops.json duration + a standard "
            f"{_PLAN_TYPE[key]} stage schedule. Fertilizer DOSES are NOT set here — retrieve "
            "them from the FRG via search_knowledge_base and attach to fertilizer_schedule_dates. "
            "Adjust N-application dates around the live forecast (delay before heavy rain)."
        ),
    }
