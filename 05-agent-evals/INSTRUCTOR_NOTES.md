# Instructor Notes — Agent Evals

## Concept map

- `CampusAgentAdapter` defines the provider-independent normalized record.
- JSONL labels encode product behavior, not prose similarity.
- `grade` separates deterministic assertions; `HUMAN_RUBRIC.md` reserves subjective review for appropriate criteria.
- `summarize` keeps overall, slice, consistency, latency, tokens, and cost visible.
- `gate_results` turns acceptable change into a CI exit code.

## Typical mistakes

- Tuning against every case and calling the same set a holdout.
- Reporting percentages without numerators, denominators, or slices.
- Timing only successful cases or including human wait time inconsistently.
- Using a model judge as ground truth without blinded order and human calibration.
- Letting pull-request CI make live paid calls.

## Rubric calibration

| Criterion | Score | Rationale |
|---|---:|---|
| Functionality | 30/30 | Baseline/candidate, cache, report, repeats, and nonzero gates work end to end. |
| Code quality | 20/20 | Adapter, labels, graders, metrics, prices, and gates are separate and inspectable. |
| Evals/testing | 35/35 | 30 labeled cases, five holdouts, five core slices, repeated runs, and all required metrics are present. |
| Documentation | 15/15 | Dataset policy, human rubric, result limits, report, failures, and ship memo are clear. |
| **Total** | **100/100** | |

## Stretch goals

No stretch goals are implemented. The small set does not justify confidence-interval claims.

