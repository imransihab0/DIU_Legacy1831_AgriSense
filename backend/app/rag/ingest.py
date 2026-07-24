"""Ingest knowledge-base documents (backend/data/kb/*.md, *.txt, *.pdf) into ChromaDB.

Usage:  cd backend && python -m app.rag.ingest
Drop additional public PDFs (BARC FRG, DAE/BRRI manuals) into data/kb/ and re-run.
"""
from pypdf import PdfReader
from ..config import KB_DIR
from .store import get_collection

CHUNK_SIZE = 1200
OVERLAP = 150


def _split_long(text: str) -> list[str]:
    text = " ".join(text.split())
    if len(text) <= CHUNK_SIZE:
        return [text] if len(text) > 40 else []
    out, i = [], 0
    while i < len(text):
        out.append(text[i : i + CHUNK_SIZE])
        i += CHUNK_SIZE - OVERLAP
    return out


def _chunk(text: str, markdown: bool) -> list[str]:
    """For markdown, keep each '##' section (one crop) intact as a chunk so
    a crop's full fertilizer dose + timing stays together; oversized sections
    are further split. For non-markdown, fall back to sliding window."""
    if not markdown or "## " not in text:
        return _split_long(text)
    parts = text.split("\n## ")
    chunks = []
    for j, part in enumerate(parts):
        section = part if j == 0 else "## " + part
        chunks.extend(_split_long(section))
    return chunks


def _read(path) -> str:
    if path.suffix.lower() == ".pdf":
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(errors="ignore")


def main():
    col = get_collection(create=True)
    existing = col.count()
    if existing:
        col.delete(ids=col.get()["ids"])
    docs, metas, ids = [], [], []
    for path in sorted(KB_DIR.iterdir()):
        if path.suffix.lower() not in (".md", ".txt", ".pdf"):
            continue
        is_md = path.suffix.lower() in (".md", ".txt")
        for j, chunk in enumerate(_chunk(_read(path), is_md)):
            docs.append(chunk)
            metas.append({"source": path.name, "chunk": j})
            ids.append(f"{path.name}-{j}")
    if not docs:
        print("No documents found in", KB_DIR)
        return
    col.add(documents=docs, metadatas=metas, ids=ids)
    print(f"Ingested {len(docs)} chunks from {len(set(m['source'] for m in metas))} documents.")


if __name__ == "__main__":
    main()
