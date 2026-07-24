"""The agent loop — multi-step planning with visible tracing.

Yields ndjson-able events as the agent works so the UI can render a live
trace (Tier 0 #8): every tool call, its parameters, and the raw result.

LLM: OpenAI tool-calling, model switchable live from the UI.
"""
import json
import time
from .. import config, db, state
from . import tools as T
from .prompts import build_system_prompt


def run_agent(session_id: str, user_message: str):
    db.add_message(session_id, "user", user_message)
    profile = db.get_profile(session_id)
    system = build_system_prompt(profile)
    history = db.get_history(session_id, limit=30)

    yield {"type": "status", "text": f"Agent started (openai · {state.current_model()})"}

    gen = _run_openai(session_id, system, history)

    final = None
    for event in gen:
        if event["type"] == "final":
            final = event["content"]
        yield event

    if final:
        db.add_message(session_id, "assistant", final)


def _timed_dispatch(session_id, name, args):
    start = time.time()
    result = T.dispatch(session_id, name, args)
    ms = round((time.time() - start) * 1000)
    return result, ms


# ---------------- OpenAI (primary) ----------------

def _run_openai(session_id, system, history):
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = state.current_model()
    messages = [{"role": "system", "content": system}] + history

    for _ in range(config.MAX_AGENT_ITERATIONS):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=T.openai_tools(),
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            yield {"type": "final", "content": msg.content or ""}
            return

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            yield {"type": "tool_call", "tool": tc.function.name, "params": args}
            result, ms = _timed_dispatch(session_id, tc.function.name, args)
            yield {"type": "tool_result", "tool": tc.function.name, "ms": ms, "result": result}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    yield {"type": "final", "content": "I hit my step limit for this turn — ask me to continue."}
