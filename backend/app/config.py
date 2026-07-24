import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
load_dotenv(BASE_DIR.parent / ".env")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "kb"
CHROMA_DIR = str(BASE_DIR / ".chroma")
DB_PATH = str(BASE_DIR / "agrisense.sqlite3")

MAX_AGENT_ITERATIONS = 10
