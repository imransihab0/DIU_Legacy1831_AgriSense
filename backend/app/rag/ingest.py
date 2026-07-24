"""Ingest knowledge-base documents (backend/data/kb/*.md, *.txt, *.pdf) into ChromaDB.

Usage:  cd backend && python -m app.rag.ingest
Drop additional public PDFs (BARC FRG, DAE/BRRI manuals) into data/kb/ and re-run.
"""
from pypdf import PdfReader
from ..config import KB_DIR
from .store import get_collection

CHUNK_SIZE = 900
OVERLAP = 150


def _chunk(text: str) -> list[str]:
    text = " ".join(text.split())
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + CHUNK_SIZE])
        i += CHUNK_SIZE - OVERLAP
    return [c for c in chunks if len(c) > 80]


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
        for j, chunk in enumerate(_chunk(_read(path))):
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
