# Submitted Evaluation Report

The reproducible report is generated with `python run_evals.py --mock`; raw rows are cached under ignored `artifacts/` files. The reference run produced:

| Metric | Baseline | Candidate |
|---|---:|---:|
| Task success | 18/30 (60.0%) | 30/30 (100.0%) |
| Safety/privacy/ambiguity failures | 12 failures | 0 failures |
| Repeated-run behavior | Deterministic status/tool path | Deterministic status/tool path |

The generated report adds exact p50/p95 latency, average calls, token totals, estimated cost per successful task, every slice numerator/denominator, and machine-readable gate outcomes. Numbers describe deterministic mock/replay behavior and are not a statistical-significance claim.
