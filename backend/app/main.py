import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, config
from .agent.loop import run_agent

app = FastAPI(title="AgriSense AI — DIU_Legacy1831")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
db.init_db()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    def stream():
        try:
            for event in run_agent(req.session_id, req.message):
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


@app.get("/api/health")
def health():
    from .rag.store import get_collection
    return {
        "provider": config.LLM_PROVIDER,
        "model": config.OPENAI_MODEL if config.LLM_PROVIDER == "openai" else config.ANTHROPIC_MODEL,
        "kb_chunks": get_collection().count(),
    }


FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
