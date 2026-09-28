# Hello, LLM — Reference Submission

This command-line chatbot uses the OpenAI Python SDK directly. It supports a one-call mode and an interactive mode, resends bounded conversation history, applies a configurable persona and temperature, explains common API errors, and reports tokens plus estimated session cost.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env for live mode.
```

Run without a key:

```bash
python chatbot.py --mock --once "Explain a mean in one sentence"
python chatbot.py --mock
pytest -q
```

Run live with a chosen persona and sampling setting:

```bash
python chatbot.py --persona "You are a Socratic statistics tutor." --temperature 0.2
```

## How it works

`ChatSession.messages` begins with one `system` message. `send()` appends the user's message, trims only the oldest complete user/assistant pairs, passes the complete remaining list to the client, and stores the assistant reply. This is why the model can use an earlier fact: the provider does not remember it; the program resends it.

`OpenAIClient` is a thin live adapter. `MockClient` implements the same protocol with deterministic local responses. Authentication, rate-limit, and network failures become small domain exceptions that the UI can explain without a traceback. Failed user turns are removed rather than silently becoming “memory.”

Cost is calculated from returned input/output usage and configurable per-million-token prices. It is labeled an estimate because cached-token pricing, provider changes, rounding, and billing rules may differ. The submitted defaults are examples; verify current provider pricing before a live class.

## Configuration experiment

The three prompt/temperature configurations and the same two test prompts are recorded in [`comparison.md`](comparison.md). Lower temperature produced steadier structure in this small sample; persona wording had a larger visible effect on tone and depth. This is descriptive evidence, not a claim that two prompts measure quality reliably.

## Design decisions and limitations

- Maximum history is expressed as complete conversation pairs, so the system instruction is never trimmed.
- The local token counter is only for mock demonstrations; live mode uses provider-reported usage.
- Retrying is left to the person rather than performed automatically, which avoids amplifying a rate limit.
- The `.env` parser intentionally supports simple `KEY=VALUE` files only.
- I would next add streaming, a budget stop, and provider-specific current price lookup.

Measured API spend for the checked-in mock run: **$0.000000**. Expected live assignment spend remains under the project estimate.

