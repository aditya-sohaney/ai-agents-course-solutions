from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from generate_corpus import generate_documents  # noqa: E402
from knowledge_agent import BM25Index, KnowledgeAgent, MemoryStore, MockModel, ingest  # noqa: E402


@pytest.fixture
def docs(tmp_path):
    paths = generate_documents(tmp_path / "docs")
    return tmp_path / "docs", paths


@pytest.fixture
def agent(tmp_path, docs):
    directory, _ = docs
    return KnowledgeAgent(MockModel(), BM25Index(ingest(directory)), MemoryStore(tmp_path / "memory.sqlite3"))


def test_corpus_meets_size_requirement(docs):
    _, paths = docs
    assert len(paths) == 6
    assert sum(len(path.read_text().split()) for path in paths) >= 6000


def test_ingestion_is_idempotent(docs):
    directory, _ = docs
    first, second = ingest(directory), ingest(directory)
    assert [chunk.citation for chunk in first] == [chunk.citation for chunk in second]


def test_retrieval_finds_expected_document(docs):
    directory, _ = docs
    hits = BM25Index(ingest(directory)).search("priority aid deadline", 3)
    assert hits[0]["document_id"] == "aid_deadlines"


def test_invalid_k_is_rejected(docs):
    directory, _ = docs
    with pytest.raises(ValueError): BM25Index(ingest(directory)).search("aid", 9)


def test_grounded_answer_has_valid_citation(agent):
    output = agent.ask("ada", "one", "When is ethics review required?")
    assert output["status"] == "answered"
    assert output["citations"][0].startswith("research_ethics#")


def test_unanswerable_question_abstains(agent):
    output = agent.ask("ada", "two", "Who coaches football?")
    assert output["citations"] == []
    assert "not have enough evidence" in output["answer"]


def test_memory_update_and_recall(agent):
    agent.ask("ada", "a", "I prefer concise answers")
    agent.ask("ada", "b", "I prefer detailed answers")
    output = agent.ask("ada", "c", "What response style do I prefer?")
    assert "detailed" in output["answer"]


def test_memory_isolated_by_user(agent):
    agent.ask("ada", "a", "I prefer concise answers")
    assert agent.memory.list("grace") == {}


def test_memory_delete(agent):
    agent.ask("ada", "a", "I prefer concise answers")
    agent.memory.forget("ada", "detail_level")
    assert agent.memory.list("ada") == {}


def test_missing_document_directory_fails(tmp_path):
    with pytest.raises(FileNotFoundError): ingest(tmp_path / "missing")


class BadCitationModel:
    def respond(self, messages):
        if not any(message["role"] == "tool" for message in messages):
            return {"type": "tool", "id": "x", "name": "search_documents", "arguments": {"query": "aid", "k": 1}}
        return {"type": "final", "answer": "unsupported [fake#chunk]", "citations": ["fake#chunk"]}


def test_unretrieved_citation_is_blocked(tmp_path, docs):
    directory, _ = docs
    bad = KnowledgeAgent(BadCitationModel(), BM25Index(ingest(directory)), MemoryStore(tmp_path / "m.sqlite3"))
    assert bad.ask("ada", "x", "aid")["status"] == "failed"


class MalformedSearchModel:
    def __init__(self): self.calls = 0
    def respond(self, messages):
        self.calls += 1
        if self.calls == 1: return {"type": "tool", "id": "x", "name": "search_documents", "arguments": {"query": "aid", "extra": 1}}
        return {"type": "final", "answer": "I do not have enough evidence in the local collection.", "citations": []}


def test_malformed_search_arguments_do_not_crash(tmp_path, docs):
    directory, _ = docs
    bad = KnowledgeAgent(MalformedSearchModel(), BM25Index(ingest(directory)), MemoryStore(tmp_path / "m.sqlite3"))
    assert bad.ask("ada", "x", "aid")["status"] == "answered"

