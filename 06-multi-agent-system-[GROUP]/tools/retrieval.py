from __future__ import annotations

import json
import re
from pathlib import Path


DATA = Path(__file__).parents[1] / "data" / "documents.json"
STOP = {"a", "an", "and", "are", "for", "how", "in", "is", "of", "on", "the", "to", "what"}


def words(text): return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP}


class Retriever:
    def __init__(self, path: Path = DATA):
        self.documents = json.loads(path.read_text(encoding="utf-8"))

    def search(self, query: str, k: int = 4):
        if not query.strip() or not 1 <= k <= 8: raise ValueError("invalid search request")
        query_words = words(query)
        ranked = []
        for document in self.documents:
            overlap = len(query_words & words(document["title"] + " " + document["text"]))
            if overlap: ranked.append((overlap, document))
        ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
        return [{**document, "chunk_id": "c1", "score": float(score)} for score, document in ranked[:k]]

