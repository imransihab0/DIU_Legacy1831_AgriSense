"""Runtime-switchable LLM settings (changeable live from the UI, no restart).

Seeded from .env at startup; the /api/model endpoint mutates the model.
The API key always comes from config/env — only the model is switchable.
"""
from . import config

# Curated model menu shown in the UI (label -> model id).
OPENAI_MODELS = [
    {"id": "gpt-5.1-mini", "label": "gpt-5.1-mini (fastest)"},
    {"id": "gpt-5.1", "label": "gpt-5.1 (balanced, default)"},
    {"id": "gpt-5.4", "label": "gpt-5.4 (higher quality)"},
    {"id": "gpt-5.5", "label": "gpt-5.5 (best quality, slower)"},
]

_state = {"openai_model": config.OPENAI_MODEL}


def provider() -> str:
    return "openai"


def current_model() -> str:
    return _state["openai_model"]


def options() -> dict:
    return {
        "provider": "openai",
        "current_model": current_model(),
        "openai_models": OPENAI_MODELS,
    }


def set_model(model_id: str) -> dict:
    if model_id in {m["id"] for m in OPENAI_MODELS}:
        _state["openai_model"] = model_id
        return {"ok": True, "provider": "openai", "current_model": current_model()}
    return {"ok": False, "error": f"unknown model {model_id}"}
