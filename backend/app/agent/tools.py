"""Tool registry: JSON schemas (OpenAI + Anthropic formats) and dispatcher."""
import functools
from ..tools import weather, market, finance, bdapps, season_plan, livestock, pest, alerts, market_intel, suppliers
from ..rag import store
from .. import db

TOOL_SPECS = [
    {
        "name": "geocode_location",
        "description": "Resolve a town/district/upazila name to coordinates using the live Open-Meteo geocoding API. Call before requesting weather.",
        "parameters": {
            "type": "object",
            "properties": {"location_name": {"type": "string", "description": "Place name, e.g. 'Bogura, Bangladesh'"}},
            "required": ["location_name"],
        },
    },
    {
        "name": "get_weather_forecast",
        "description": "LIVE weather forecast (Open-Meteo, real API): daily rain, temperatures, rain probability for up to 16 days. All weather statements MUST come from this tool.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "days": {"type": "integer", "description": "1-16, default 14"},
            },
            "required": ["latitude", "longitude"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "RAG search over the agronomy knowledge base (BARC fertilizer guide, DAE/BRRI crop calendars, pest management, soil/water guides). Use for fertilizer doses, sowing windows, pest advice, soil suitability. Cite the returned source names.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "description": "default 4"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_market_prices",
        "description": "Crop OUTPUT prices — what the farmer SELLS (paddy, potato, mustard seed as a commodity...), BDT/kg, seeded catalog. Use for revenue/sell-side questions. Optionally filter by crop.",
        "parameters": {
            "type": "object",
            "properties": {"crop": {"type": "string", "description": "e.g. 'potato' (optional)"}},
            "required": [],
        },
    },
    {
        "name": "get_input_prices",
        "description": "Farm INPUT prices — what the farmer BUYS: fertilizers (urea, TSP, MoP, gypsum, zinc, boron), seeds (mustard, wheat, boro rice, lentil, potato...), and pesticides. BDT per bag/kg from a seeded reference catalog. ALWAYS call this when the farmer asks about product prices, a price list, what to buy, or wants to purchase inputs — never state input prices from memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "optional: 'fertilizers', 'seeds', or 'pesticides'"},
                "item": {"type": "string", "description": "optional single item, e.g. 'urea' or 'mustard'"},
            },
            "required": [],
        },
    },
    {
        "name": "compute_financials",
        "description": "Deterministic financial engine: itemized costs, yield, revenue, net profit, ROI, break-even for a crop and area. ALL money math must come from this tool. Supports scenario overrides: yield_factor / cost_factor / price_factor (e.g. 0.7 = 30% lower).",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "one of: boro_rice, aman_rice, wheat, maize, potato, mustard, lentil, onion, jute, tomato"},
                "area_acres": {"type": "number"},
                "budget_bdt": {"type": "number", "description": "farmer's budget, to check affordability"},
                "price_per_kg": {"type": "number", "description": "override price if farmer states one"},
                "yield_factor": {"type": "number", "description": "scenario multiplier, default 1.0"},
                "cost_factor": {"type": "number", "description": "scenario multiplier, default 1.0"},
                "price_factor": {"type": "number", "description": "scenario multiplier, default 1.0"},
            },
            "required": ["crop", "area_acres"],
        },
    },
    {
        "name": "generate_season_plan",
        "description": "Deterministic DATED season calendar for the CHOSEN crop: land prep, sowing/transplanting, fertilizer split dates, irrigation, weed/pest checkpoints, harvest — computed in Python from the crop's duration and a standard agronomic schedule, with validation. ALWAYS call this to build the calendar (Tier 0 #4) instead of writing dates yourself. It returns only TIMING; get fertilizer DOSES from search_knowledge_base (FRG) and attach them, and shift N-application dates around the live forecast.",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "one of: boro_rice, aman_rice, wheat, maize, potato, mustard, lentil, onion, jute, tomato"},
                "start_date": {"type": "string", "description": "sowing (direct) or transplanting date, YYYY-MM-DD. Omit to derive the next upcoming date from the crop's sowing window."},
                "area_acres": {"type": "number"},
                "soil_type": {"type": "string"},
            },
            "required": ["crop"],
        },
    },
    {
        "name": "assess_pest_risk",
        "description": "Deterministic pest & disease RISK for a crop, scored from the LIVE weather (temperature + moisture) and the crop's current growth stage. Returns each likely threat with a risk level (high/medium/low), symptoms, prevention, treatment and an indicative per-acre cost. Call this for pest/disease questions and when building or reviewing a plan — pass temp_c and recent_rain_mm from get_weather_forecast and growth_stage from the season plan. Pair with search_knowledge_base for detail.",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "one of: boro_rice, aman_rice, wheat, maize, potato, mustard, lentil, onion, jute, tomato"},
                "growth_stage": {"type": "string", "description": "e.g. 'seedling', 'vegetative', 'tillering', 'flowering', 'tuber bulking', 'fruiting', 'maturity'"},
                "temp_c": {"type": "number", "description": "current/avg temperature °C from the live forecast"},
                "humidity_pct": {"type": "number", "description": "relative humidity % if known"},
                "recent_rain_mm": {"type": "number", "description": "recent/forecast rain mm over ~a week from the live forecast"},
                "area_acres": {"type": "number", "description": "to total the treatment cost"},
            },
            "required": ["crop"],
        },
    },
    {
        "name": "compute_livestock_financials",
        "description": "Deterministic livestock financial engine (animals, not crops): itemized costs, output (live weight / milk / eggs), revenue, net profit, ROI, break-even for a batch over one production cycle. Use for ANY animal profit/cost question (broiler, layer, goat_fattening, beef_fattening, dairy_cow). ALL animal money math must come from this tool. Supports scenario overrides: yield_factor / cost_factor / price_factor and a mortality_pct override.",
        "parameters": {
            "type": "object",
            "properties": {
                "animal": {"type": "string", "description": "one of: broiler, layer, goat_fattening, beef_fattening, dairy_cow"},
                "count": {"type": "number", "description": "number of animals/birds; omit to use a typical batch size"},
                "price_override": {"type": "number", "description": "override sale price (per kg for meat, per litre milk, per egg) if the farmer states one"},
                "yield_factor": {"type": "number", "description": "scenario multiplier on output per animal, default 1.0"},
                "cost_factor": {"type": "number", "description": "scenario multiplier on costs, default 1.0"},
                "price_factor": {"type": "number", "description": "scenario multiplier on price, default 1.0"},
                "mortality_pct": {"type": "number", "description": "override mortality percentage for a scenario"},
                "budget_bdt": {"type": "number", "description": "farmer's budget, to check affordability"},
            },
            "required": ["animal"],
        },
    },
    {
        "name": "generate_livestock_plan",
        "description": "Deterministic DATED rearing + vaccination calendar for an animal batch: procurement/placement, vaccination & deworming dates, feed-phase changes, health/weight checkpoints, and sale/end-of-cycle — computed in Python from the cycle length and a standard DLS/BLRI schedule, with validation. ALWAYS call this to build an animal's schedule instead of writing dates yourself. Pair with search_knowledge_base for feeding/disease detail.",
        "parameters": {
            "type": "object",
            "properties": {
                "animal": {"type": "string", "description": "one of: broiler, layer, goat_fattening, beef_fattening, dairy_cow"},
                "count": {"type": "number", "description": "number of animals/birds (optional)"},
                "start_date": {"type": "string", "description": "cycle start (chick placement / procurement / calving) YYYY-MM-DD; omit to start today"},
            },
            "required": ["animal"],
        },
    },
    {
        "name": "check_weather_alerts",
        "description": "Proactively check the farm's saved season plan against the LIVE forecast and return weather-triggered alerts (e.g. heavy rain near a nitrogen-application or sowing date -> delay it; rain near an irrigation date -> skip it). Uses the persisted plan + farm location automatically. Call this when the farmer asks 'any warnings?', after building a plan, or to give proactive advice. Offer to send an urgent alert as SMS via bdapps_send_sms.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "market_price_intelligence",
        "description": "Crop SELL-side market intelligence: current price, a modeled 12-month price history/seasonal range, and a deterministic SELL-NOW / STORE / WAIT recommendation that accounts for the seasonal trend, storage cost and spoilage. Use when the farmer asks whether to sell now or hold, or about price trends. Prices are seeded/labeled.",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "crop or price key, e.g. potato, boro_rice, onion"},
                "max_store_months": {"type": "integer", "description": "how many months the farmer could store; default 6"},
            },
            "required": ["crop"],
        },
    },
    {
        "name": "compare_suppliers",
        "description": "Compare input DEALERS/suppliers for an item (fertilizer/seed/pesticide) ranked by price, delivery time, distance and rating, from a seeded supplier catalog. Use when the farmer asks where to buy cheapest/fastest/nearest, or wants to compare dealers before purchasing.",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "input item key, e.g. urea, tsp, mop, dap, mancozeb, cartap, imidacloprid"},
                "quantity": {"type": "number", "description": "quantity to total the line cost (optional)"},
                "sort_by": {"type": "string", "description": "price | delivery | distance | rating (default price)"},
            },
            "required": ["item"],
        },
    },
    {
        "name": "save_farm_profile",
        "description": "Persist farm profile fields to memory (survives across sessions). Call as soon as the farmer reveals any field.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "farm_size_acres": {"type": "number"},
                "soil_type": {"type": "string"},
                "water_availability": {"type": "string"},
                "budget_bdt": {"type": "number"},
                "target_season": {"type": "string"},
                "chosen_crop": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "bdapps_query_balance",
        "description": "bdapps CaaS queryBalance (POST /caas/get/balance): check a subscriber's mobile-account chargeable balance before charging. Use when the farmer asks their balance or before a large purchase.",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriber_number": {"type": "string", "description": "e.g. 8801812345678"},
            },
            "required": ["subscriber_number"],
        },
    },
    {
        "name": "bdapps_send_sms",
        "description": "Send an SMS to the farmer's phone via bdapps (POST /sms/send; Bengali auto-encoded). Use for proactive weather-triggered alerts (e.g. 'Heavy rain in 4 days — delay urea application') or plan reminders, when the farmer asks for SMS alerts.",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriber_number": {"type": "string", "description": "e.g. 8801812345678"},
                "message": {"type": "string", "description": "short alert text, Bengali or English, max ~300 chars"},
            },
            "required": ["subscriber_number", "message"],
        },
    },
    {
        "name": "bdapps_checkout",
        "description": "bdapps CaaS complete checkout flow (official TAP API shapes): queryBalance -> directDebit (POST /caas/direct/debit) -> SMS receipt (POST /sms/send). Charges the farmer's mobile balance for an input purchase and returns every request/response pair plus the receipt. Only call AFTER the farmer confirms the purchase and gives their mobile number.",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriber_number": {"type": "string", "description": "e.g. 8801812345678"},
                "amount_bdt": {"type": "number"},
                "description": {"type": "string", "description": "what is being purchased, e.g. '60 kg wheat seed'"},
            },
            "required": ["subscriber_number", "amount_bdt", "description"],
        },
    },
]


def openai_tools() -> list[dict]:
    return [{"type": "function", "function": s} for s in TOOL_SPECS]


def anthropic_tools() -> list[dict]:
    return [
        {"name": s["name"], "description": s["description"], "input_schema": s["parameters"]}
        for s in TOOL_SPECS
    ]


def dispatch(session_id: str, name: str, args: dict):
    try:
        if name == "geocode_location":
            return weather.geocode_location(**args)
        if name == "get_weather_forecast":
            return weather.get_weather_forecast(**args)
        if name == "search_knowledge_base":
            return store.search_knowledge_base(**args)
        if name == "get_market_prices":
            return market.get_market_prices(**args)
        if name == "get_input_prices":
            return market.get_input_prices(**args)
        if name == "compute_financials":
            return finance.compute_financials(**args)
        if name == "generate_season_plan":
            result = season_plan.generate_season_plan(**args)
            if isinstance(result, dict) and "error" not in result:
                db.save_plan(session_id, result)  # persist for proactive weather alerts
            return result
        if name == "assess_pest_risk":
            return pest.assess_pest_risk(**args)
        if name == "check_weather_alerts":
            return alerts.check_weather_alerts(session_id)
        if name == "market_price_intelligence":
            return market_intel.market_price_intelligence(**args)
        if name == "compare_suppliers":
            return suppliers.compare_suppliers(**args)
        if name == "compute_livestock_financials":
            return livestock.compute_livestock_financials(**args)
        if name == "generate_livestock_plan":
            return livestock.generate_livestock_plan(**args)
        if name == "save_farm_profile":
            return {"saved_profile": db.save_profile(session_id, args)}
        if name == "bdapps_query_balance":
            return bdapps.query_balance(**args)
        if name == "bdapps_send_sms":
            return bdapps.send_sms(**args)
        if name == "bdapps_checkout":
            return bdapps.bdapps_checkout(**args)
        return {"error": f"Unknown tool {name}"}
    except Exception as e:  # tool errors go back to the model, not the user
        return {"error": f"{type(e).__name__}: {e}"}
