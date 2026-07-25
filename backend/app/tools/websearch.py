"""Web-search fallback — fetch farming info NOT in the KB, and append it to the KB.

Last resort when search_knowledge_base has no answer (e.g. a price/variety/fact not
in the vetted docs). Results are labeled UNVERIFIED and written to the RAG store with
source "web (unverified)" so they're kept clearly separate from the trusted gov docs
and can be retrieved next time without re-searching. A fresh `python -m app.rag.ingest`
wipes them (rebuilds the vetted KB from files), so web junk never permanently pollutes it.
"""
import time
from datetime import date

from ..rag import store

WEB_SOURCE = "web (unverified)"


def _append_to_kb(query: str, items: list[dict]):
    """Save the web findings into ChromaDB, clearly tagged as unverified."""
    body = "\n".join(f"- {i['title']}: {i['snippet']} ({i['url']})"
                     for i in items if i.get("snippet"))
    if not body:
        return
    text = f"Web search result for '{query}' (fetched {date.today().isoformat()}, UNVERIFIED):\n{body}"
    col = store.get_collection(create=True)
    col.add(
        documents=[text],
        metadatas=[{"source": WEB_SOURCE, "chunk": 0, "verified": False, "query": query}],
        ids=[f"web-{abs(hash(query))}-{int(time.time())}"],
    )


def web_search(query: str, num_results: int = 5) -> dict:
    """Search the web for farming info not in the KB; append results to the KB (unverified)."""
    try:
        from ddgs import DDGS
        raw = DDGS().text(query, max_results=min(int(num_results), 8))
    except Exception as e:
        return {"error": f"Web search unavailable ({type(e).__name__}). Fall back to the KB/catalog, "
                "or tell the farmer to check the local source; do not invent an answer."}
    items = [{"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
             for r in (raw or [])]
    if not items:
        return {"query": query, "results": [], "note": "No web results found."}
    _append_to_kb(query, items)
    return {
        "query": query,
        "results": items,
        "source": WEB_SOURCE,
        "saved_to_kb": True,
        "disclaimer": "These are UNVERIFIED web results, not from the trusted knowledge base. "
        "Present them as indicative/web-sourced, cite that they're from the web, and suggest the "
        "farmer confirm locally. Never present web data as authoritative gov/KB data.",
    }
