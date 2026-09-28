from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import asdict
from pathlib import Path

from agents.reviewer import ClaimReviewer
from agents.scout import EvidenceScout
from agents.writer import BriefWriter
from contracts import EvidenceItem, ResearchRequest
from tools.retrieval import Retriever


class ResearchOrchestrator:
    def __init__(self, trace_path: Path | None = None):
        self.scout, self.reviewer, self.writer = EvidenceScout(Retriever()), ClaimReviewer(), BriefWriter()
        self.trace_path = trace_path
        self.calls = 0

    def _trace(self, role, artifact_ids, status, started, retry=0):
        event = {"role": role, "artifact_ids": artifact_ids, "status": status, "latency_ms": round((time.perf_counter()-started)*1000, 3), "usage_tokens": 0, "estimated_cost": 0.0, "retry": retry}
        if self.trace_path:
            with self.trace_path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, sort_keys=True)+"\n")

    def run(self, request: ResearchRequest, inject: str | None = None):
        started = time.perf_counter(); self.calls = 0
        if inject == "empty":
            brief = self.writer.write(request.question, [], [])
            self._trace("orchestrator", [], "partial", started); return brief
        queries = [request.question, request.question + " implementation evidence"]
        gathered = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.scout.gather, query, request.max_sources // 2 + 1) for query in queries]
            for index, future in enumerate(futures):
                self.calls += 1
                try:
                    if inject == "timeout" and index == 0: raise TimeoutError()
                    gathered.extend(future.result(timeout=2))
                except TimeoutError:
                    self._trace("EvidenceScout", [], "timeout", started)
        unique = {item.evidence_id: item for item in gathered}
        items = list(unique.values())[: request.max_sources]
        if inject == "malformed" and items:
            first = items[0]
            items[0] = EvidenceItem(first.evidence_id, "unsupported changed claim", first.document_id, first.chunk_id, first.excerpt, first.score)
        self._trace("EvidenceScout", [item.evidence_id for item in items], "ok" if items else "empty", started)
        self.calls += 1
        decisions = self.reviewer.review(items)
        self._trace("ClaimReviewer", [decision.evidence_id for decision in decisions], "ok", started)
        accepted_ids = {decision.evidence_id for decision in decisions if decision.verdict != "reject"}
        accepted_items = [item for item in items if item.evidence_id in accepted_ids]
        accepted_decisions = [decision for decision in decisions if decision.evidence_id in accepted_ids]
        self.calls += 1
        status = "partial" if inject in {"timeout", "malformed"} else "complete"
        brief = self.writer.write(request.question, accepted_items, accepted_decisions, status)
        if self.calls > 8: raise RuntimeError("role-call budget exceeded")
        self._trace("BriefWriter", list(brief.citations), brief.status, started)
        return brief


def baseline(question: str):
    hits = EvidenceScout(Retriever()).gather(question, 3)
    citations = tuple(item.citation for item in hits)
    return {"status": "complete" if hits else "partial", "citations": citations, "unsupported_claims": 1 if hits else 0}

