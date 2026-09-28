# AI Agents Course — Reference Solutions

Private instructor-only reference implementations for the projects in `ai-agents-course-projects`. These are strong, intentionally compact student-style submissions: clear enough to teach from, complete enough to run, and small enough for students to understand. Do not link this repository from the public course materials.

> **Current handoff status:** Reference solutions for Projects 1–6 are complete and tested offline. Projects 7–8 are intentionally listed as pending after the September 28, 2026 checkpoint; their folders have not been published as incomplete work.

## Index

| # | Solution | Offline smoke command |
|---:|---|---|
| 1 | [Hello, LLM](01-hello-llm/) | `python chatbot.py --mock --once "Remember that my name is Ada"` |
| 2 | [Your First AI Agent](02-your-first-ai-agent/) | `python agent.py --mock "What is (17 * 4) + 9?"` |
| 3 | [Reliable Tool-Use Agent](03-tool-use-agent/) | `python campus_agent.py --mock "Convert 5 miles to kilometers"` |
| 4 | [Stateful Knowledge Agent](04-memory-and-rag-agent/) | `python knowledge_agent.py --mock ask --user ada "When is quiet hour?"` |
| 5 | [Agent Evals](05-agent-evals/) | `python run_evals.py --mock` |
| 6 | [Research Brief Studio `[GROUP]`](06-multi-agent-system-[GROUP]/) | `python -m ui.cli --mock "What improves student retention?"` |
| 7 | Operations Orchestrator `[GROUP]` — **pending** | Not yet published |
| 8A | Capstone: Research Assistant — **pending** | Not yet published |
| 8B | Capstone: Local Business Support — **pending** | Not yet published |

## Running a solution

Each folder is self-contained and has its own pinned `requirements.txt`, `.env.example`, tests, student-style `README.md`, `INSTRUCTOR_NOTES.md`, and sample output. From a solution folder:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Every command supports `--mock` or `MOCK_LLM=1`. Mock mode uses deterministic local responses, needs no API key or network access, and is the mode used by the tests. Live mode uses the OpenAI Python SDK and reads `OPENAI_API_KEY` from the environment.

## Instructor guidance

- Use the student README to demonstrate what a polished submission looks like.
- Use `INSTRUCTOR_NOTES.md` to connect files to objectives, anticipate misconceptions, and calibrate rubric scores.
- Re-run sample/evaluation commands before a term begins; live model behavior and provider prices can change.
- Never distribute this complete repository to a current class. Extract only the narrow excerpts needed for instruction.
