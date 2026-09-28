# Sample Run

```text
$ python generate_corpus.py
generated 6 documents with 21306 words

$ python knowledge_agent.py --mock ask --user ada "When is ethics review required?"
{
  "status": "answered",
  "answer": "Research involving living people requires ethics review before recruitment or data collection begins. [research_ethics#... ]",
  "citations": ["research_ethics#..."]
}

$ python knowledge_agent.py --mock ask --user ada "Who coaches football?"
{
  "status": "answered",
  "answer": "I do not have enough evidence in the local collection.",
  "citations": []
}

$ python run_evals.py
...
{"retrieval_hit_rate": 1.0, "abstention_success": 1.0, "memory_success": 1.0}
```

Chunk hashes are deterministic but abbreviated above for readability.
