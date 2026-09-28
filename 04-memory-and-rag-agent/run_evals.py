import json
import tempfile
from pathlib import Path

from generate_corpus import generate_documents
from knowledge_agent import BM25Index, KnowledgeAgent, MemoryStore, MockModel, ingest


def main():
    cases = [json.loads(line) for line in (Path(__file__).parent / "evals" / "cases.jsonl").read_text().splitlines() if line]
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        generate_documents(root / "docs")
        agent = KnowledgeAgent(MockModel(), BM25Index(ingest(root / "docs")), MemoryStore(root / "memory.sqlite3"))
        results = []
        for case in cases:
            user = "other-user" if case["type"] == "isolation" else "ada"
            output = agent.ask(user, case["id"], case["question"])
            if case["type"] == "document":
                passed = any(citation.startswith(case["expected_document"] + "#") for citation in output["citations"])
            elif case["type"] == "unanswerable":
                passed = not output["citations"] and "not have enough evidence" in output["answer"]
            elif case["type"] == "memory":
                passed = "saved" in output["answer"].lower()
            elif case["type"] == "memory_recall":
                passed = case["expected"] in output["answer"].lower()
            elif case["type"] == "memory_update":
                passed = agent.memory.list("ada")["detail_level"]["value"] == case["expected"]
            else:
                passed = "not saved" in output["answer"].lower()
            results.append({"id": case["id"], "passed": passed})
            print(json.dumps(results[-1]))
        document = [result for result, case in zip(results, cases) if case["type"] == "document"]
        unknown = [result for result, case in zip(results, cases) if case["type"] == "unanswerable"]
        print(json.dumps({"retrieval_hit_rate": sum(item["passed"] for item in document) / len(document), "abstention_success": sum(item["passed"] for item in unknown) / len(unknown), "memory_success": sum(item["passed"] for item, case in zip(results, cases) if case["type"] not in {"document", "unanswerable"}) / 4}, indent=2))
        return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

