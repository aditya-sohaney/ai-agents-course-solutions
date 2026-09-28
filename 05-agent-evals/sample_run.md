# Sample Run

```text
$ python run_evals.py --mock
{
  "baseline": {"success": 18, "total": 30, "success_rate": 0.6, ...},
  "candidate": {"success": 30, "total": 30, "success_rate": 1.0, ...},
  "gates": {
    "success": true,
    "latency": true,
    "cost": true,
    "protected_slices": true
  }
}
```

The command writes normalized baseline/candidate JSONL and a generated Markdown report under `artifacts/`.
