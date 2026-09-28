from __future__ import annotations

import hashlib
import re

from contracts import EvidenceItem


class EvidenceScout:
    def __init__(self, retriever): self.retriever = retriever

    def gather(self, query: str, k: int = 4):
        items = []
        for hit in self.retriever.search(query, k):
            claim = re.split(r"(?<=[.!?])\s+", hit["text"])[0]
            evidence_id = hashlib.sha1(f"{hit['id']}:{claim}".encode()).hexdigest()[:10]
            items.append(EvidenceItem(evidence_id, claim, hit["id"], hit["chunk_id"], hit["text"], hit["score"]))
        return items

