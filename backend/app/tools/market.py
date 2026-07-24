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
    if crop:
        key = crop.lower().strip().replace(" ", "_")
        if key in prices:
            prices = {key: prices[key]}
    return {
        "disclaimer": "SEEDED/MOCK crop-OUTPUT price catalog (labeled per rules) — not a live feed.",
        "currency": data["currency"],
        "unit": data["unit"],
        "prices": prices,
    }


def get_input_prices(category: str | None = None, item: str | None = None) -> dict:
    data = json.loads((DATA_DIR / "input_prices.json").read_text())
    cats = {"fertilizers": data["fertilizers"], "seeds": data["seeds"], "pesticides": data["pesticides"]}
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
