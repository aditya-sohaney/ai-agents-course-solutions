"""Run baseline/candidate cases, repeats, metrics, report, and regression gates."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from agent_under_test import CampusAgentAdapter


ROOT = Path(__file__).parent


def load_cases(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def grade(case, record):
    checks = {
        "schema": set(record.final_output) == {"status", "answer", "tools_used", "error"},
        "expected_status": record.status == case["expected_status"],
        "required_tools": all(tool in record.tool_trace for tool in case["required_tools"]),
        "forbidden_tools": all(tool not in record.tool_trace for tool in case["forbidden_tools"]),
        "loop_limit": record.model_calls <= 5,
    }
    return {"passed": all(checks[name] for name in case["deterministic_assertions"]), "checks": checks}


def percentile(values, fraction):
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def summarize(cases, rows):
    by_id = {row["record"]["case_id"]: row for row in rows if row["repeat"] == 0}
    successes = sum(by_id[case["id"]]["grade"]["passed"] for case in cases)
    slice_counts = defaultdict(lambda: [0, 0])
    for case in cases:
        passed = by_id[case["id"]]["grade"]["passed"]
        for tag in case["tags"]:
            slice_counts[tag][1] += 1
            slice_counts[tag][0] += passed
    records = [row["record"] for row in rows if row["repeat"] == 0]
    successful = max(1, successes)
    repeat_groups = defaultdict(set)
    for row in rows:
        repeat_groups[row["record"]["case_id"]].add((row["record"]["status"], tuple(row["record"]["tool_trace"])))
    return {
        "success": successes,
        "total": len(cases),
        "success_rate": successes / len(cases),
        "slices": {tag: {"passed": counts[0], "total": counts[1], "rate": counts[0] / counts[1]} for tag, counts in sorted(slice_counts.items())},
        "p50_latency_ms": statistics.median(record["latency_ms"] for record in records),
        "p95_latency_ms": percentile([record["latency_ms"] for record in records], 0.95),
        "average_model_calls": statistics.mean(record["model_calls"] for record in records),
        "total_tokens": sum(record["input_tokens"] + record["output_tokens"] for record in records),
        "total_cost": sum(record["estimated_cost"] for record in records),
        "cost_per_success": sum(record["estimated_cost"] for record in records) / successful,
        "consistency_rate": sum(len(outcomes) == 1 for outcomes in repeat_groups.values()) / len(repeat_groups),
    }


def gate_results(baseline, candidate, gates):
    success_drop = (baseline["success_rate"] - candidate["success_rate"]) * 100
    latency_rise = (candidate["p95_latency_ms"] / baseline["p95_latency_ms"] - 1) * 100
    cost_rise = (candidate["cost_per_success"] / baseline["cost_per_success"] - 1) * 100
    protected = all(
        candidate["slices"].get(tag, {"rate": 1})["rate"] >= baseline["slices"].get(tag, {"rate": 1})["rate"]
        for tag in gates["protected_tags"]
    )
    return {
        "success": success_drop <= gates["max_success_drop_points"],
        "latency": latency_rise <= gates["max_p95_latency_increase_percent"],
        "cost": cost_rise <= gates["max_cost_per_success_increase_percent"],
        "protected_slices": protected,
        "observed": {"success_drop_points": success_drop, "p95_latency_increase_percent": latency_rise, "cost_per_success_increase_percent": cost_rise},
    }


def render_report(baseline, candidate, gates):
    return f"""# Generated Evaluation Report

| Metric | Baseline | Candidate |
|---|---:|---:|
| Task success | {baseline['success']}/{baseline['total']} ({baseline['success_rate']:.1%}) | {candidate['success']}/{candidate['total']} ({candidate['success_rate']:.1%}) |
| p50 latency | {baseline['p50_latency_ms']:.0f} ms | {candidate['p50_latency_ms']:.0f} ms |
| p95 latency | {baseline['p95_latency_ms']:.0f} ms | {candidate['p95_latency_ms']:.0f} ms |
| Average model calls | {baseline['average_model_calls']:.2f} | {candidate['average_model_calls']:.2f} |
| Total tokens | {baseline['total_tokens']} | {candidate['total_tokens']} |
| Cost per success | ${baseline['cost_per_success']:.6f} | ${candidate['cost_per_success']:.6f} |
| Repeated-run consistency | {baseline['consistency_rate']:.1%} | {candidate['consistency_rate']:.1%} |

Candidate slice results: {json.dumps(candidate['slices'], sort_keys=True)}

Regression gates: {json.dumps(gates, sort_keys=True)}

The 30-case sample is too small for a statistical-significance claim. Metrics compare one deterministic replay configuration and are intended to demonstrate the harness.
"""


def run(output: Path):
    cases = load_cases(ROOT / "evals" / "cases.jsonl")
    repeated_ids = {case["id"] for case in cases[:10]}
    summaries = {}
    output.mkdir(parents=True, exist_ok=True)
    for version in ("baseline", "candidate"):
        adapter = CampusAgentAdapter(version)
        rows = []
        for case in cases:
            repeats = range(3) if case["id"] in repeated_ids else range(1)
            for repeat in repeats:
                record = adapter.run(case["id"], case["input"], repeat).to_dict()
                rows.append({"repeat": repeat, "record": record, "grade": grade(case, type("Record", (), record)())})
        with (output / f"{version}.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows: handle.write(json.dumps(row, sort_keys=True) + "\n")
        summaries[version] = summarize(cases, rows)
    config = json.loads((ROOT / "regression_gates.json").read_text())
    gates = gate_results(summaries["baseline"], summaries["candidate"], config)
    (output / "generated-report.md").write_text(render_report(summaries["baseline"], summaries["candidate"], gates), encoding="utf-8")
    print(json.dumps({"baseline": summaries["baseline"], "candidate": summaries["candidate"], "gates": gates}, indent=2, sort_keys=True))
    return 0 if all(value for key, value in gates.items() if key != "observed") else 1


def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--mock", action="store_true"); parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args(argv)
    return run(args.output)


if __name__ == "__main__": raise SystemExit(main())

