# Your First AI Agent — Reference Submission

This is the smallest inspectable agent I could build: one model, one calculator tool, and a three-call limit. The model chooses whether to request the tool; Python validates and executes it; the observation returns to the model before the final answer.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python agent.py --mock "What is (17 * 4) + 9?"
python agent.py --mock "What is a confidence interval?"
python agent.py --mock "Use unsupported code to calculate this"
```

For live mode, copy `.env.example` to `.env`, export its values in your shell, and omit `--mock`. The API key is never logged. The model's output is capped at 250 tokens and each request makes no more than three model calls.

## The loop in five lines

1. Send the user message and one calculator schema to the model.
2. If the model answers, stop.
3. If it requests the calculator, validate its name and arguments.
4. Execute safe AST arithmetic and append the JSON observation as a tool message.
5. Ask the model again, stopping after three total calls.

## Design decisions

`calculate` walks an allowlisted Python AST; it never calls `eval`. It limits expression length, nesting, supported operators, and result magnitude. Every result—including a rejection—is a structured observation. `CalculatorAgent` owns the loop and trace, while both live and mock models implement one small protocol.

Trace events expose iteration, requested tool, validated arguments, observation, latency, and stop reason. They deliberately omit keys and hidden reasoning. The mock is a model double, not a second implementation of the calculator, so tests exercise the production loop.

## Limitations and improvements

The expression extraction in mock mode exists only for deterministic demonstrations. The calculator has no exponentiation and uses floating-point arithmetic. I would next add JSON-schema validation at the provider boundary and `Decimal` for domains that need exact cents.

Measured cost for the checked-in mock runs: **$0.00**. A live acceptance pass uses two calls for arithmetic and one for a direct answer, within the assignment estimate.

