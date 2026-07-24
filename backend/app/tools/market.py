"""Seeded price catalogs — clearly labeled per hackathon rules.

- get_market_prices: CROP OUTPUT prices (what the farmer SELLS: paddy, potato...).
- get_input_prices:  FARM INPUT prices (what the farmer BUYS: fertilizer, seed,
  pesticide). Powers the input cart + bdapps checkout.
"""
import json
from ..config import DATA_DIR


def get_market_prices(crop: str | None = None) -> dict:
    data = json.loads((DATA_DIR / "market_prices.json").read_text())
    prices = data["prices"]
    note = None
    if crop:
        q = crop.lower().strip().replace(" ", "_")
        matches = {
            k: v for k, v in prices.items()
            if q == k or q in k or k in q or q.replace("_", " ") in v["crop"].lower()
        }
        if matches:
            prices = matches
        else:
            prices = {}
            note = (f"'{crop}' is not in the seeded price catalog. Tell the farmer this specific "
                    "crop isn't in our reference prices (suggest checking the local bazar/DAM), then "
                    "offer cultivation + cost/profit help. Do NOT invent a price.")
    return {
        "disclaimer": "SEEDED/MOCK crop-OUTPUT price catalog (labeled per rules) — not a live feed. Prices are indicative BDT/kg; confirm at the local market.",
        "currency": data["currency"],
        "unit": data["unit"],
        "prices": prices,
        **({"note": note} if note else {}),
    }


def get_input_prices(category: str | None = None, item: str | None = None) -> dict:
    data = json.loads((DATA_DIR / "input_prices.json").read_text())
    cats = {"fertilizers": data["fertilizers"], "seeds": data["seeds"],
            "pesticides": data["pesticides"], "livestock": data.get("livestock", {})}
    if category:
        c = category.lower().strip()
        cats = {c: cats[c]} if c in cats else cats
    if item:
        key = item.lower().strip().replace(" ", "_")
        cats = {cat: {key: items[key]} for cat, items in cats.items() if key in items} or cats
    return {
        "disclaimer": "SEEDED reference INPUT prices (BADC/DAE-indicative, labeled) — not a live feed. Advise the farmer to confirm at their local dealer.",
        "currency": data["currency"],
        "catalog": cats,
    }
