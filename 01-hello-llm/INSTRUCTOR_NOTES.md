# Instructor Notes — Hello, LLM

## Concept walkthrough

- **API request/response:** `OpenAIClient.complete` is the only provider-specific boundary. The rest of the program depends on the `ChatClient` protocol.
- **Roles and history:** `ChatSession` owns one list beginning with a system message. The second-turn test proves the full prior exchange reaches the client.
- **System prompt and temperature:** both are explicit constructor/CLI inputs; `comparison.md` treats observations cautiously.
- **Tokens and cost:** `Usage` accumulates provider metadata, and `estimate_cost` keeps price assumptions configurable.
- **Errors:** domain exceptions separate user-facing recovery from changing SDK exception names.

## Where students get stuck

- They append only user messages, so prior assistant replies disappear.
- They assume the provider stores a conversation automatically.
- They trim `messages[:N]` and accidentally remove the system prompt.
- They commit `.env`, print the key during debugging, or place a real key in `.env.example`.
- They calculate all tokens at one price, forget “per million,” or present a local word count as provider billing.
- They catch `Exception` in the UI and display a traceback instead of classifying expected failures.

## Rubric calibration

| Criterion | Score | Rationale |
|---|---:|---|
| Functionality | 40/40 | Both modes, bounded history, persona, errors, live usage, and session cost are implemented. |
| Code quality | 20/20 | Small protocol boundary, domain errors, safe configuration, and pure cost function keep concerns clear. |
| Evals/testing | 25/25 | Ten test cases cover message roles, two-turn state, trimming, cost, errors, failed state, exit, and accumulation. |
| Documentation | 15/15 | Setup, architecture, comparison, sample transcript, limitations, and spend are present. |
| **Total** | **100/100** | Strong reference submission. |

## Stretch goals

No stretch goals are implemented. That is intentional: the example prioritizes the required fundamentals and avoids teaching file persistence before students understand in-memory history.

