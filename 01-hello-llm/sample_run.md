# Sample Run (Mock Mode)

```text
$ python chatbot.py --mock
Persona: You are a patient study buddy for introductory statistics.
You: My name is Ada
Bot: Study-buddy reply: My name is Ada
Usage: in=22, out=9; session estimate=$0.000023
You: What is my name?
Bot: Your name is Ada.
Usage: in=34, out=5; session estimate=$0.000044
You: exit
Session ended.

$ python chatbot.py --mock --mock-error rate --once "hello"
Could not get a response: Rate limit reached. Wait briefly, then retry.
```

Mock usage is a deterministic approximation for teaching. Live mode prints provider-reported token counts.

