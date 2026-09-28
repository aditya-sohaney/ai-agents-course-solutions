# Instructor Notes — Your First AI Agent

## Concept walkthrough

- `TOOL_SCHEMA` is the model-facing affordance; `calculate` is the actual permission boundary.
- `CalculatorAgent.run` shows prompt → requested call → validated execution → observation → final response without framework indirection.
- `MockModel` makes the same decision/observation loop testable without money or a key.
- `TraceEvent` exposes behavior without asking for or logging chain-of-thought.

## Common sticking points

- Students execute the tool but forget to append its result with the matching tool-call ID.
- They use `eval`, regex alone, or an AST visitor that accidentally allows names/calls.
- They trust the schema to validate arguments; schemas guide models but Python still enforces rules.
- They count tool calls but not model calls, leaving an unbounded loop.
- Their mock bypasses the agent and therefore cannot detect a broken observation handoff.

## Rubric calibration

| Criterion | Score | Rationale |
|---|---:|---|
| Functionality | 40/40 | Exactly one tool, safe execution, structured failure, explicit observation handoff, direct answer, and three-call bound. |
| Code quality | 20/20 | Model, loop, calculator, trace, and CLI are distinct without unnecessary abstraction. |
| Evals/testing | 25/25 | Nine tests cover four arithmetic forms, two rejection paths, tool handoff, direct response, and loop bound. |
| Documentation | 15/15 | Setup, loop explanation, acceptance examples, limitations, safety, and spend are documented. |
| **Total** | **100/100** | |

## Stretch goals

No stretch goal is implemented. In particular, exponentiation stays excluded so the allowlist remains easy to audit.

