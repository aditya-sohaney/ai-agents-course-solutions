# Instructor Notes — Reliable Tool-Use Agent

## Learning-objective map

- **Tool design:** `TOOL_SCHEMAS` uses distinct names, closed enums, required fields, and no extras.
- **Untrusted output:** `validate_args` runs before `_dispatch`; schema hints alone never grant permission.
- **Structured final output:** `validate_final` checks the exact contract and the loop permits one repair.
- **Failure handling:** forced outages become observations, while repeated calls and budgets stop deterministically.
- **No memory:** `messages` is local to `run`; every CLI invocation/request begins cleanly.

## Typical mistakes

- Reusing a module-level messages list and accidentally adding memory.
- Returning three different error shapes from three tools.
- Treating an unsupported conversion as zero or silently choosing a unit.
- Retrying a deterministic validation error until the loop limit.
- Logging prompts or credentials when only event metadata is needed.

## Rubric calibration

| Criterion | Score | Rationale |
|---|---:|---|
| Functionality | 40/40 | Three tools, strict final contract, stateless loop, bounds, forced failure, and honest statuses work. |
| Code quality | 20/20 | Common envelopes and explicit validation keep the compact single-file example readable. |
| Evals/testing | 25/25 | Fifteen tests plus all six acceptance cases cover required paths. |
| Documentation | 15/15 | Contracts, architecture, errors, limits, results, cost, and limitations are documented. |
| **Total** | **100/100** | |

## Stretch goals

No stretch goals are implemented. The three required tools and reliability behavior remain the teaching focus.

