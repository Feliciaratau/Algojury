import json
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
CHUNKS_PATH = BASE / "knowledge" / "chunks.json"
SOURCES_PATH = BASE / "corpus" / "sources.json"

def _load(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))

def retrieve(query: str, limit: int = 6) -> list[dict[str, Any]]:
    chunks = _load(CHUNKS_PATH)
    q = query.lower()
    terms = {t for t in q.replace("/", " ").replace("-", " ").split() if len(t) > 2}
    scored = []
    for chunk in chunks:
        haystack = " ".join([
            chunk.get("text", ""),
            chunk.get("locator", ""),
            " ".join(chunk.get("tags", []))
        ]).lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]

def source_map() -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in _load(SOURCES_PATH)}

def enrich(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = source_map()
    out = []
    for c in chunks:
        item = dict(c)
        item["source"] = sources.get(c["source_id"], {})
        out.append(item)
    return out
