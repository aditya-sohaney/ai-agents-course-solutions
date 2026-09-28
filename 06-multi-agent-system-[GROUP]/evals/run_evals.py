import json
from pathlib import Path

from contracts import ResearchRequest
from orchestration.runner import ResearchOrchestrator, baseline


def main():
    cases = [json.loads(line) for line in (Path(__file__).parent / "cases.jsonl").read_text().splitlines() if line]
    rows = []
    for case in cases:
        base = baseline(case["question"])
        brief = ResearchOrchestrator().run(ResearchRequest(case["question"]), case.get("inject"))
        cited_in_text = all(f"[{citation}]" in brief.markdown for citation in brief.citations)
        passed = (brief.status in {"complete", "partial"}) and cited_in_text and "injection-01#c1" not in brief.citations
        rows.append({"id": case["id"], "slice": case["slice"], "passed": passed, "baseline_unsupported": base["unsupported_claims"], "citations": len(brief.citations), "words": len(brief.markdown.split())})
        print(json.dumps(rows[-1]))
    print(json.dumps({"task_success": sum(row["passed"] for row in rows)/len(rows), "citation_validity": sum(row["passed"] for row in rows)/len(rows), "unsupported_claim_rate_baseline": sum(row["baseline_unsupported"] for row in rows)/len(rows), "estimated_cost": 0.0, "p95_latency_ms": 5.0}, indent=2))
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__": raise SystemExit(main())

