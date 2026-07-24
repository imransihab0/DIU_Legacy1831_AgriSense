import json
import sqlite3
import time
from .config import DB_PATH


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS farms (
                session_id TEXT PRIMARY KEY,
                profile TEXT NOT NULL,
                updated_at REAL NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts REAL NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS plans (
                session_id TEXT PRIMARY KEY,
                plan TEXT NOT NULL,
                updated_at REAL NOT NULL
            )"""
        )


def save_plan(session_id: str, plan: dict):
    with _conn() as c:
        c.execute(
            "INSERT INTO plans(session_id, plan, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET plan=excluded.plan, updated_at=excluded.updated_at",
            (session_id, json.dumps(plan, ensure_ascii=False), time.time()),
        )


def get_plan(session_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT plan FROM plans WHERE session_id=?", (session_id,)).fetchone()
    return json.loads(row["plan"]) if row else None


def get_profile(session_id: str) -> dict:
    with _conn() as c:
        row = c.execute(
            "SELECT profile FROM farms WHERE session_id=?", (session_id,)
        ).fetchone()
    return json.loads(row["profile"]) if row else {}


def save_profile(session_id: str, updates: dict) -> dict:
    profile = get_profile(session_id)
    profile.update({k: v for k, v in updates.items() if v not in (None, "", [])})
    with _conn() as c:
        c.execute(
            "INSERT INTO farms(session_id, profile, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET profile=excluded.profile, updated_at=excluded.updated_at",
            (session_id, json.dumps(profile, ensure_ascii=False), time.time()),
        )
    return profile


def add_message(session_id: str, role: str, content: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO messages(session_id, role, content, ts) VALUES(?,?,?,?)",
            (session_id, role, content, time.time()),
        )


def get_history(session_id: str, limit: int = 30) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def reset_session(session_id: str):
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        c.execute("DELETE FROM farms WHERE session_id=?", (session_id,))
        c.execute("DELETE FROM plans WHERE session_id=?", (session_id,))
