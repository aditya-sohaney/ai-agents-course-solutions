# Sample Run

```text
$ python campus_agent.py --mock "Calculate 2 + 2 and convert 5 miles to kilometers"
{
  "answer": "4; 8.0467",
  "error": null,
  "status": "answered",
  "tools_used": ["calculator", "convert_units"]
}

$ python campus_agent.py --mock --fail-tool lookup_policy "What are quiet hours?"
{
  "answer": "I could not complete the request with verified tool data.",
  "error": "TOOL_UNAVAILABLE",
  "status": "failed",
  "tools_used": ["lookup_policy"]
}

$ python run_evals.py
...
summary: 6/6 passed
```

