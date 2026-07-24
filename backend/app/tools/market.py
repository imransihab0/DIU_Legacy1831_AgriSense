"""Seeded market price catalog — clearly labeled MOCK per hackathon rules."""
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
        "disclaimer": "SEEDED/MOCK price catalog (labeled per rules) — not a live feed.",
        "currency": data["currency"],
        "unit": data["unit"],
        "prices": prices,
    }
