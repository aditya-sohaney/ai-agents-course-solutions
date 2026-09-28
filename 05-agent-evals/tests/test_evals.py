from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from agent_under_test import CampusAgentAdapter  # noqa: E402
from run_evals import ROOT, gate_results, grade, load_cases, run, summarize  # noqa: E402


def cases(): return load_cases(ROOT / "evals" / "cases.jsonl")


def test_dataset_has_30_cases_and_five_holdouts():
    data = cases(); assert len(data) == 30; assert sum(case["holdout"] for case in data) == 5


def test_dataset_has_required_slices():
    tags = {tag for case in cases() for tag in case["tags"]}
    assert {"normal", "ambiguous", "tool_failure", "adversarial", "domain"} <= tags


def test_normalized_record_contains_all_metrics():
    record = CampusAgentAdapter("candidate").run("x", "Calculate 1 + 1")
    assert record.model_calls and record.input_tokens and record.output_tokens
    assert record.latency_ms > 0 and record.estimated_cost > 0


def test_deterministic_grader_catches_forbidden_tool():
    case = next(case for case in cases() if case["id"] == "attack-01")
    record = CampusAgentAdapter("baseline").run(case["id"], case["input"])
    assert not grade(case, record)["passed"]


def test_candidate_handles_ambiguity():
    case = next(case for case in cases() if case["id"] == "ambiguous-01")
    record = CampusAgentAdapter("candidate").run(case["id"], case["input"])
    assert grade(case, record)["passed"]


def test_repeat_path_is_consistent():
    adapter = CampusAgentAdapter("candidate")
    outcomes = {(adapter.run("x", "Calculate 2 + 2", i).status, tuple(adapter.run("x", "Calculate 2 + 2", i).tool_trace)) for i in range(3)}
    assert len(outcomes) == 1


def test_gates_pass_for_improvement():
    baseline = {"success_rate": .5, "p95_latency_ms": 200, "cost_per_success": .001, "slices": {"safety": {"rate": 0}, "privacy": {"rate": 0}}}
    candidate = {"success_rate": 1, "p95_latency_ms": 220, "cost_per_success": .0008, "slices": {"safety": {"rate": 1}, "privacy": {"rate": 1}}}
    config = json.loads((ROOT / "regression_gates.json").read_text())
    assert all(value for key, value in gate_results(baseline, candidate, config).items() if key != "observed")


def test_end_to_end_generates_cached_rows_and_report(tmp_path):
    assert run(tmp_path) == 0
    assert (tmp_path / "baseline.jsonl").exists()
    assert (tmp_path / "candidate.jsonl").exists()
    assert "Task success" in (tmp_path / "generated-report.md").read_text()

