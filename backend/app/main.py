import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, config, state
from .agent.loop import run_agent

app = FastAPI(title="AgriSense AI — DIU_Legacy1831")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.middleware("http")
async def no_cache_frontend(request, call_next):
    """Serve the HTML/JS/CSS with no-cache so code changes always load (no stale browser cache)."""
    response = await call_next(request)
    p = request.url.path
    if p == "/" or p.endswith((".js", ".css", ".html")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


db.init_db()


from typing import Optional

class ChatRequest(BaseModel):
    session_id: str
    message: str
    image_data_url: Optional[str] = None


@app.post("/api/chat")
def chat(req: ChatRequest):
    def stream():
        try:
            for event in run_agent(req.session_id, req.message, req.image_data_url):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "text": f"{type(e).__name__}: {e}"}) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.get("/api/profile/{session_id}")
def profile(session_id: str):
    return db.get_profile(session_id)


@app.post("/api/reset/{session_id}")
def reset(session_id: str):
    db.reset_session(session_id)
    return {"ok": True}


@app.get("/api/inputs")
def inputs():
    """Seeded input catalog (fertilizer/seed/pesticide) for the order-builder dialog."""
    from .tools import market
    return market.get_input_prices()


@app.get("/api/alerts/{session_id}")
def alerts_endpoint(session_id: str):
    """Proactive weather alerts for the farm's saved plan — polled by the UI (no chat turn)."""
    from .tools import alerts
    return alerts.get_session_alerts(session_id)


@app.get("/api/health")
def health():
    from .rag.store import get_collection
    return {
        "provider": state.provider(),
        "model": state.current_model(),
        "kb_chunks": get_collection().count(),
    }


@app.get("/api/model")
def get_model():
    return state.options()


class ModelRequest(BaseModel):
    model: str


@app.post("/api/model")
def set_model(req: ModelRequest):
    return state.set_model(req.model)


FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
