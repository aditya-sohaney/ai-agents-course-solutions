# `integration-v1` Milestone Evidence

At the end-of-week-1 checkpoint, `contracts.py` is the frozen v1 handoff surface. `tests/test_integration.py` constructs the real retriever, Evidence Scout, Claim Reviewer, Brief Writer, and orchestrator; it verifies a 600–900 word cited brief and trace events from every role. The test runs in offline CI with deterministic documents.

Ownership: Student A — `tools/` and `agents/scout.py`; Student B — `contracts.py` and `orchestration/`; Student C — `agents/reviewer.py`, `evals/`, and traces; Student D — `agents/writer.py`, `ui/`, and documentation. In a three-person team, A also owns the UI. Every safety-sensitive boundary receives a cross-owner review.

