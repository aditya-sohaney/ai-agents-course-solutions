from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchRequest:
    question: str
    max_sources: int = 6

    def __post_init__(self):
        if not self.question.strip() or not 1 <= self.max_sources <= 8:
            raise ValueError("question and max_sources are invalid")


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    claim: str
    document_id: str
    chunk_id: str
    excerpt: str
    score: float

    @property
    def citation(self): return f"{self.document_id}#{self.chunk_id}"


@dataclass(frozen=True)
class ReviewDecision:
    evidence_id: str
    verdict: str
    reason: str

    def __post_init__(self):
        if self.verdict not in {"accept", "reject", "conflict"}:
            raise ValueError("invalid review verdict")


@dataclass(frozen=True)
class FinalBrief:
    status: str
    markdown: str
    citations: tuple[str, ...]
    stop_reason: str

