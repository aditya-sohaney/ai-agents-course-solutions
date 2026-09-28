# Measure What Matters — Reference Submission

This evaluation harness compares a preserved baseline with one candidate change. It normalizes outputs, grades 30 versioned cases, repeats ten cases three times per system, caches raw rows, reports quality/cost/latency, and exits nonzero when a regression gate fails.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python run_evals.py --mock
```

`CampusAgentAdapter` is a deterministic stand-in for the Project 3/4 adapter, so the complete reference runs with no key. Replace only that adapter to point the same harness at a live agent. CI uses replay/mock behavior and never calls a provider.

## Dataset and labels

`evals/cases.jsonl` has 30 IDs across normal, ambiguous, tool-failure, adversarial, domain, safety, privacy, and holdout tags. Five holdouts are marked and were not used to design the candidate behavior. Each row declares expected status, required/forbidden tools, exact deterministic assertions, and a label rationale.

Deterministic checks grade schemas, statuses, tool traces, and loop bounds. `HUMAN_RUBRIC.md` defines a blinded rubric for nuanced answer quality. No model judge is used, avoiding unneeded cost and judge calibration in this compact example.

## Results and decision

The submitted mock run improves task success from **18/30 to 30/30** by clarifying underspecified requests and blocking unauthorized/privacy actions. The generated report includes slice numerators/denominators, p50/p95 latency, average model calls, total tokens, estimated cost per success, and repeat consistency. All configured gates pass. See `decision_memo.md` for the ship decision and three failure categories.

These are replay results, not claims about a production model or statistical significance. Live evaluation would need provider runs, human review, and more independent cases. Mock cost is **$0.00**; the harness still records per-case estimated cost fields.

## Improvements

I would add case-author review, paired confidence intervals only after increasing sample size, and a small filterable static report. I would also hash case versions to reveal when a tuned prompt has seen a former holdout.
