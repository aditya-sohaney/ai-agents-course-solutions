# Decision Memo — Ship the Candidate

The candidate should ship to the next test environment. On the checked-in deterministic run it improves task success from 60% to 100%, including all safety and privacy cases. Its p95 latency remains inside the 25% gate and cost per successful task improves because fewer requests end in an incorrect “success.”

Three baseline failure categories drove the result. First, ambiguous prompts were converted into guesses instead of clarification. Second, prompt-injection cases reached a forbidden `send_message` action that the agent did not actually own. Third, cross-user requests disclosed a memorized preference. The candidate adds explicit clarification and deny behavior for those categories.

This is not proof of production quality. The set has only 30 authored cases, five holdouts, and deterministic replay timing. Before release I would add paraphrases written by someone who did not author the prompt, run against a live provider at least three times, and manually review nuanced answers using `HUMAN_RUBRIC.md`.
