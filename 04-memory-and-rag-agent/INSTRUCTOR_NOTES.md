# Instructor Notes — Stateful Knowledge Agent

## Learning-objective map

- `KnowledgeAgent.sessions` and `MemoryStore` make short-term state and durable memory visibly different.
- `generate_corpus`, `ingest`, and `BM25Index` expose every RAG stage without a framework.
- `retrieved_ids` is the citation allowlist for a turn; `BadCitationModel` proves the verifier blocks inventions.
- Memory rows contain user ID, allowlisted key, value, direct-statement provenance, and timestamp; inspect/forget are first-class commands.
- The evaluation runner reports retrieval, abstention, and memory categories separately.

## Common sticking points

- Treating the transcript as durable memory or sharing a single memory namespace across users.
- Saving an assistant inference instead of a directly stated preference.
- Chunk IDs that change on every run, making labels and citations impossible to reproduce.
- Measuring final prose while never checking whether the expected document was retrieved.
- Allowing a plausible citation that was not present in the current retrieval result.

## Rubric calibration

| Criterion | Score | Rationale |
|---|---:|---|
| Functionality | 40/40 | Raw tools, local retrieval, verified citations, abstention, bounded state, and isolated inspectable/deletable memory work. |
| Code quality | 20/20 | Generator, ingestion, retrieval, memory, model adapter, orchestration, and verification are explicit. |
| Evals/testing | 25/25 | Twelve tests plus 15 labeled cases cover corpus, idempotence, retrieval, citation, memory, isolation, deletion, and failures. |
| Documentation | 15/15 | Architecture, provenance, state policy, metrics, commands, costs, and limitations are documented. |
| **Total** | **100/100** | |

## Stretch goals

No stretch goals are implemented. The simple BM25 baseline makes later retrieval comparisons meaningful.

