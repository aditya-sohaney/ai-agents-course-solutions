# Sample Run

```text
$ python agent.py --mock "What is (17 * 4) + 9?"
{"arguments": {"expression": "(17 * 4) + 9"}, "event": "tool_call", "iteration": 1, "latency_ms": 0.01, "observation": {"error": null, "ok": true, "result": 77}, "stop_reason": null, "tool": "calculator"}
{"arguments": null, "event": "final", "iteration": 2, "latency_ms": 0.01, "observation": null, "stop_reason": "model_answer", "tool": null}
Response: The answer is 77.

$ python agent.py --mock "Use unsupported code to calculate this"
... "observation": {"ok": false, "result": null, "error": "unsupported syntax: Call"} ...
Response: I could not calculate that safely: unsupported syntax: Call
```

