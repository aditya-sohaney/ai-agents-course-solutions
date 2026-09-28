# Sample Run

```text
$ python -m ui.cli --mock "What improves student retention?"
# Research Brief

## Executive summary
This brief examines: **What improves student retention?** ...

## Findings
- Proactive advising messages ... [advising-01#c1]
- Small emergency grants ... [financial-01#c1]
...
status=complete stop=completed citations=6

$ python -m evals.run_evals
...
{"task_success": 1.0, "citation_validity": 1.0, "estimated_cost": 0.0}
```

