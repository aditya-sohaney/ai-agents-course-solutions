from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from agents.reviewer import ClaimReviewer  # noqa: E402
from agents.scout import EvidenceScout  # noqa: E402
from agents.writer import BriefWriter  # noqa: E402
from contracts import EvidenceItem, ResearchRequest  # noqa: E402
from orchestration.runner import ResearchOrchestrator  # noqa: E402
from tools.retrieval import Retriever  # noqa: E402


def test_request_contract_rejects_blank():
    with pytest.raises(ValueError): ResearchRequest("")


def test_retriever_returns_stable_source_ids():
    assert Retriever().search("mentoring")[0]["id"].startswith("mentoring-")


def test_scout_creates_evidence_contracts():
    items = EvidenceScout(Retriever()).gather("mentoring")
    assert items and all(item.claim in item.excerpt for item in items)


def test_reviewer_rejects_embedded_instruction():
    items = EvidenceScout(Retriever()).gather("untrusted prompt injection")
    decisions = ClaimReviewer().review(items)
    assert any(decision.verdict == "reject" for decision in decisions)


def test_reviewer_preserves_conflict():
    items = EvidenceScout(Retriever()).gather("peer mentoring completion")
    decisions = ClaimReviewer().review(items)
    assert sum(decision.verdict == "conflict" for decision in decisions) >= 2


def test_writer_produces_required_length_and_citations():
    items = EvidenceScout(Retriever()).gather("mentoring retention")
    decisions = ClaimReviewer().review(items)
    brief = BriefWriter().write("Does mentoring help?", items, decisions)
    assert 600 <= len(brief.markdown.split()) <= 900
    assert all(f"[{citation}]" in brief.markdown for citation in brief.citations)


def test_empty_retrieval_returns_partial():
    assert ResearchOrchestrator().run(ResearchRequest("football score"), "empty").status == "partial"


def test_timeout_returns_bounded_partial_result():
    brief = ResearchOrchestrator().run(ResearchRequest("student retention"), "timeout")
    assert brief.status == "partial"


def test_malformed_handoff_is_rejected_not_crashed():
    brief = ResearchOrchestrator().run(ResearchRequest("peer mentoring"), "malformed")
    assert brief.status == "partial"

