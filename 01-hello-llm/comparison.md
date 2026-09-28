# Prompt and Temperature Comparison

Prompts used in every configuration:

1. “Explain why a mean can be misleading.”
2. “Give me a two-question practice check.”

| Configuration | System prompt | Temperature | Observed output summary |
|---|---|---:|---|
| A | Patient study buddy for introductory statistics | 0.2 | Short definitions, one concrete outlier example, consistent numbered quiz. |
| B | Socratic statistics tutor who answers with questions | 0.7 | More follow-up questions and less direct exposition; quiz wording varied. |
| C | Concise exam coach who prioritizes formulas and traps | 1.0 | Denser vocabulary, formula notation, and more varied examples and warnings. |

Across these six short calls, the system prompt changed the visible teaching strategy more than temperature did. Configuration A answered directly and used a stable example about salaries. Configuration B regularly responded with a question before explaining, which felt interactive but sometimes delayed the definition. Configuration C emphasized exam cues and formulas; it was useful for review but assumed more prior knowledge.

Temperature appeared to affect variation, not factual capability. At 0.2, repeated phrasing and list structure were more consistent. At 0.7, examples and follow-up questions changed more. At 1.0, the answer used livelier wording but once introduced an extra concept that the prompt did not require. This tiny comparison is not an evaluation: each configuration was run only once per prompt, provider sampling is nondeterministic, and prompt wording changed at the same time as temperature. A stronger experiment would vary one factor at a time and repeat each condition. For this assignment, the useful lesson is that the system message establishes priorities while temperature adjusts sampling within the model's supported range. I would choose A for a beginning student because its tone and structure were predictable.

