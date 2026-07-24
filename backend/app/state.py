"""Runtime-switchable LLM settings (changeable live from the UI, no restart).

Seeded from .env at startup; the /api/model endpoint mutates these.
API keys always come from config/env — only provider + model are switchable.
"""
from . import config

# Curated model menu shown in the UI (label -> model id).
OPENAI_MODELS = [
    {"id": "gpt-5.1-mini", "label": "gpt-5.1-mini (fastest)"},
    {"id": "gpt-5.1", "label": "gpt-5.1 (balanced, default)"},
    {"id": "gpt-5.4", "label": "gpt-5.4 (higher quality)"},
    {"id": "gpt-5.5", "label": "gpt-5.5 (best quality, slower)"},
]
ANTHROPIC_MODELS = [
    {"id": "claude-sonnet-4-6", "label": "claude-sonnet-4-6"},
    {"id": "claude-opus-4-8", "label": "claude-opus-4-8"},
]

_state = {
    "provider": config.LLM_PROVIDER,
    "openai_model": config.OPENAI_MODEL,
    "anthropic_model": config.ANTHROPIC_MODEL,
}


def provider() -> str:
    return _state["provider"]


def current_model() -> str:
    return _state["openai_model"] if _state["provider"] == "openai" else _state["anthropic_model"]


def options() -> dict:
    return {
        "provider": _state["provider"],
        "current_model": current_model(),
        "openai_models": OPENAI_MODELS,
        "anthropic_models": ANTHROPIC_MODELS,
        "anthropic_key_set": bool(config.ANTHROPIC_API_KEY and "..." not in config.ANTHROPIC_API_KEY),
    }


def set_model(model_id: str) -> dict:
    known_openai = {m["id"] for m in OPENAI_MODELS}
    known_anthropic = {m["id"] for m in ANTHROPIC_MODELS}
    if model_id in known_openai:
        _state["provider"] = "openai"
        _state["openai_model"] = model_id
    elif model_id in known_anthropic:
        _state["provider"] = "anthropic"
        _state["anthropic_model"] = model_id
    else:
        return {"ok": False, "error": f"unknown model {model_id}"}
    return {"ok": True, "provider": _state["provider"], "current_model": current_model()}
