# Reliable Tool-Use Agent — Reference Submission

The Campus Utility Agent is one stateless model that can calculate, convert four distance units, and look up eight fictional campus policies. Every tool shares the same `{ok, data, error_code, message}` envelope, and the final answer has a separately validated contract.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python campus_agent.py --mock "Convert 5 miles to kilometers"
python campus_agent.py --mock --fail-tool lookup_policy "What are quiet hours?"
python run_evals.py
```

Live mode uses the official OpenAI SDK when `--mock` is omitted and `OPENAI_API_KEY` is exported. Automated tests and CI use mock mode and make no network calls.

## Architecture and contracts

`CampusAgent` creates a fresh message list for every `run`, so it cannot remember an earlier command. It allows five model calls and three tool calls, rejects identical repeated calls, validates tool names/arguments in Python, and gives failures back to the model as observations. One repair instruction is allowed for an invalid final object.

The model-facing schemas use enums and `additionalProperties: false`; Python repeats the checks because model output is untrusted. JSONL trace records contain request ID, event, tool, latency, success, and a sanitized error code. User answers never depend on parsing those logs.

## Acceptance results

`python run_evals.py` reports **6/6** in deterministic mock mode: one case per tool, a two-tool request, an ambiguous request, and a forced failure. Fifteen unit/integration cases cover success, failure, schema validation, loop control, trace structure, and the final contract.

## Limitations and improvements

The dataset is fictional and the converter intentionally supports only four units. Live final-JSON support can vary by provider/model. I would next use a dedicated JSON Schema validator, add per-tool timeouts, and compare alternative tool descriptions on the acceptance set.

Mock spend is **$0.00**. Live runs are capped and fit within the assignment estimate.

