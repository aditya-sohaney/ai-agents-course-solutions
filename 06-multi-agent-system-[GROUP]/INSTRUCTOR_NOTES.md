# Instructor Notes — Research Brief Studio

## Module boundaries

- **Student A:** `tools/retrieval.py` and `agents/scout.py` own source IDs and evidence extraction.
- **Student B:** `contracts.py` and `orchestration/runner.py` own routing, deduplication, concurrency, budgets, and recovery.
- **Student C:** `agents/reviewer.py`, `evals/`, and trace fields own verification and measurement.
- **Student D:** `agents/writer.py`, `ui/`, README, and demo own synthesis and user experience.
- `tests/test_integration.py` is the mid-project shared contract; nobody can change its dataclasses unilaterally.

## Common mistakes

- Passing free-form prose instead of versioned artifacts.
- Letting specialists call each other or mutate shared history invisibly.
- Treating more agents as the outcome instead of comparing with one agent.
- Removing conflicting evidence during synthesis or following instructions inside retrieved text.
- Waiting until the final week to run an end-to-end contract test.

## Rubric calibration

| Criterion | Score | Rationale |
|---|---:|---|
| Functionality | 35/35 | Distinct roles, parallel/sequential flow, citations, bounds, conflict, injection, and required failures work. |
| Code quality | 15/15 | Role directories and frozen dataclasses make ownership and interfaces obvious. |
| Evals/testing | 25/25 | Component, integration, and 20-case baseline-comparison evidence is runnable offline. |
| Documentation | 15/15 | Diagrams, milestone, ADR, roles, demo, limits, and cost are present. |
| Peer evaluation | 10/10 | Reference assumes corroborated ownership and cross-review described in `MILESTONE.md`; real teams submit private forms. |
| **Total** | **100/100** | |

## Stretch goals

No stretch goals are implemented. The ADR identifies targeted retrieval and an ablation as appropriate next work.

