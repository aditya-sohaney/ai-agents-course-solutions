from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from contracts import ResearchRequest  # noqa: E402
from orchestration.runner import ResearchOrchestrator  # noqa: E402


def test_integration_v1_all_roles_share_contracts(tmp_path):
    trace = tmp_path / "trace.jsonl"
    brief = ResearchOrchestrator(trace).run(ResearchRequest("What improves student retention?"))
    assert brief.status == "complete"
    assert 600 <= len(brief.markdown.split()) <= 900
    assert brief.citations
    events = trace.read_text().splitlines()
    assert any('"role": "EvidenceScout"' in line for line in events)
    assert any('"role": "ClaimReviewer"' in line for line in events)
    assert any('"role": "BriefWriter"' in line for line in events)

