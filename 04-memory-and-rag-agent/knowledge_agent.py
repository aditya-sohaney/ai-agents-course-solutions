"""Raw-SDK state, local BM25 retrieval, durable memory, and citation checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from generate_corpus import generate_documents


STOP_WORDS = {"a", "an", "and", "are", "at", "be", "campus", "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "the", "to", "what", "when"}


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]


@dataclass(frozen=True)
class Chunk:
    document_id: str
    chunk_id: str
    title: str
    source_path: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.document_id}#{self.chunk_id}"


def ingest(directory: Path, words_per_chunk: int = 150, overlap: int = 30) -> list[Chunk]:
    if not directory.exists():
        raise FileNotFoundError("document directory is missing; run generate_corpus.py")
    chunks: dict[str, Chunk] = {}
    for path in sorted(directory.glob("*.md")):
        content = " ".join(path.read_text(encoding="utf-8").split())
        words = content.split()
        title = path.stem.replace("_", " ").title()
        step = words_per_chunk - overlap
        for index, start in enumerate(range(0, len(words), step)):
            text = " ".join(words[start : start + words_per_chunk])
            if not text:
                continue
            digest = hashlib.sha1(f"{path.stem}:{index}:{text}".encode()).hexdigest()[:10]
            chunk = Chunk(path.stem, digest, title, str(path), text)
            chunks[chunk.citation] = chunk
    return [chunks[key] for key in sorted(chunks)]


class BM25Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.documents = [tokens(chunk.text) for chunk in chunks]
        self.avg_length = sum(map(len, self.documents)) / len(self.documents) if self.documents else 0
        self.document_frequency = Counter()
        for document in self.documents:
            self.document_frequency.update(set(document))

    def search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        if type(k) is not int or not 1 <= k <= 5:
            raise ValueError("k must be an integer from 1 to 5")
        query_terms = tokens(query)
        if not query_terms or not self.documents:
            return []
        scored = []
        for chunk, document in zip(self.chunks, self.documents):
            frequencies = Counter(document)
            score = 0.0
            for term in query_terms:
                df = self.document_frequency.get(term, 0)
                if not df:
                    continue
                idf = math.log(1 + (len(self.documents) - df + 0.5) / (df + 0.5))
                tf = frequencies[term]
                denominator = tf + 1.5 * (1 - 0.75 + 0.75 * len(document) / self.avg_length)
                score += idf * (tf * 2.5 / denominator)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].citation))
        return [
            {"score": round(score, 6), "document_id": chunk.document_id, "chunk_id": chunk.chunk_id, "title": chunk.title, "text": chunk.text}
            for score, chunk in scored[:k]
        ]


class MemoryStore:
    ALLOWED_KEYS = {"detail_level", "preferred_topic"}

    def __init__(self, path: Path):
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS memories (user_id TEXT, key TEXT, value TEXT, provenance TEXT, updated_at TEXT, PRIMARY KEY(user_id, key))"
        )

    def set(self, user_id: str, key: str, value: str, provenance: str):
        if key not in self.ALLOWED_KEYS or not value.strip():
            raise ValueError("memory key or value is not allowed")
        self.connection.execute(
            "INSERT INTO memories VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value, provenance=excluded.provenance, updated_at=excluded.updated_at",
            (user_id, key, value.strip(), provenance, datetime.now(timezone.utc).isoformat()),
        )
        self.connection.commit()

    def list(self, user_id: str) -> dict[str, dict[str, str]]:
        rows = self.connection.execute(
            "SELECT key, value, provenance, updated_at FROM memories WHERE user_id=? ORDER BY key", (user_id,)
        ).fetchall()
        return {row[0]: {"value": row[1], "provenance": row[2], "updated_at": row[3]} for row in rows}

    def forget(self, user_id: str, key: str | None = None):
        if key:
            self.connection.execute("DELETE FROM memories WHERE user_id=? AND key=?", (user_id, key))
        else:
            self.connection.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
        self.connection.commit()


TOOLS = [
    {"type": "function", "function": {"name": "search_documents", "description": "Retrieve grounded local evidence.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer", "minimum": 1, "maximum": 5}}, "required": ["query", "k"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "save_preference", "description": "Save a preference directly stated by the user.", "parameters": {"type": "object", "properties": {"key": {"type": "string", "enum": ["detail_level", "preferred_topic"]}, "value": {"type": "string"}}, "required": ["key", "value"], "additionalProperties": False}}},
]


class Model(Protocol):
    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


class MockModel:
    def respond(self, messages):
        user = next(message["content"] for message in reversed(messages) if message["role"] == "user")
        lowered = user.lower()
        tools = [message for message in messages if message["role"] == "tool"]
        system = messages[0]["content"]
        if "i prefer" in lowered and not tools:
            value = "concise" if "concise" in lowered else "detailed" if "detailed" in lowered else lowered.split("i prefer", 1)[1].strip()
            return {"type": "tool", "id": "memory-1", "name": "save_preference", "arguments": {"key": "detail_level", "value": value}}
        if "what response style" in lowered:
            match = re.search(r"detail_level': \{'value': '([^']+)'", system)
            value = match.group(1) if match else None
            return {"type": "final", "answer": f"You prefer {value} answers." if value else "You have not saved a response style.", "citations": []}
        if tools and tools[-1].get("name") == "save_preference":
            observation = json.loads(tools[-1]["content"])
            return {"type": "final", "answer": "I saved that preference." if observation["ok"] else "I could not save that preference.", "citations": []}
        search_tools = [message for message in tools if message.get("name") == "search_documents"]
        if not search_tools:
            return {"type": "tool", "id": "search-1", "name": "search_documents", "arguments": {"query": user, "k": 3}}
        observation = json.loads(search_tools[-1]["content"])
        hits = observation.get("data", [])
        if not hits:
            return {"type": "final", "answer": "I do not have enough evidence in the local collection.", "citations": []}
        hit = hits[0]
        sentences = re.split(r"(?<=[.!?])\s+", hit["text"])
        query_terms = set(tokens(user))
        sentence = max(
            sentences,
            key=lambda candidate: (len(query_terms.intersection(tokens(candidate))), -len(candidate)),
        )
        citation = f"{hit['document_id']}#{hit['chunk_id']}"
        return {"type": "final", "answer": f"{sentence} [{citation}]", "citations": [citation]}


class OpenAIModel:
    def __init__(self, model: str, api_key: str | None):
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def respond(self, messages):
        response = self.client.chat.completions.create(model=self.model, messages=messages, tools=TOOLS, response_format={"type": "json_object"}, max_tokens=400)
        message = response.choices[0].message
        if message.tool_calls:
            call = message.tool_calls[0]
            try: arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError: arguments = None
            return {"type": "tool", "id": call.id, "name": call.function.name, "arguments": arguments}
        try:
            payload = json.loads(message.content or "{}")
            return {"type": "final", "answer": payload.get("answer", ""), "citations": payload.get("citations", [])}
        except json.JSONDecodeError:
            return {"type": "final", "answer": "I could not form a valid grounded answer.", "citations": []}


class KnowledgeAgent:
    def __init__(self, model: Model, index: BM25Index, memory: MemoryStore, trace_path: Path | None = None):
        self.model, self.index, self.memory, self.trace_path = model, index, memory, trace_path
        self.sessions: dict[str, list[dict[str, str]]] = {}

    def _log(self, event: dict[str, Any]):
        if self.trace_path:
            with self.trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

    def ask(self, user_id: str, session_id: str, question: str) -> dict[str, Any]:
        history = self.sessions.setdefault(session_id, [])[-6:]
        saved = self.memory.list(user_id)
        messages: list[dict[str, Any]] = [{"role": "system", "content": f"Answer only from retrieved chunks. Durable memory: {saved}. Return answer and citations as JSON."}, *history, {"role": "user", "content": question}]
        retrieved_ids: set[str] = set()
        retrieval_calls = 0
        events = []
        for call_number in range(1, 6):
            started = time.perf_counter()
            response = self.model.respond(messages)
            latency = round((time.perf_counter() - started) * 1000, 3)
            if response.get("type") == "final":
                citations = response.get("citations", [])
                if any(citation not in retrieved_ids for citation in citations):
                    return {"status": "failed", "answer": "Citation verification failed.", "citations": [], "events": events}
                answer = response.get("answer", "")
                self.sessions[session_id] = (history + [{"role": "user", "content": question}, {"role": "assistant", "content": answer}])[-6:]
                events.append({"event": "final", "latency_ms": latency, "citations": citations, "stop_reason": "answer"})
                self._log({"user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:8], **events[-1]})
                return {"status": "answered", "answer": answer, "citations": citations, "events": events}
            name, args = response.get("name"), response.get("arguments")
            if name == "search_documents":
                retrieval_calls += 1
                if retrieval_calls > 2 or not isinstance(args, dict) or set(args) != {"query", "k"}:
                    observation = {"ok": False, "data": [], "error": "INVALID_SEARCH"}
                else:
                    try:
                        hits = self.index.search(args["query"], args["k"])
                        observation = {"ok": True, "data": hits, "error": None}
                        retrieved_ids.update(f"{hit['document_id']}#{hit['chunk_id']}" for hit in hits)
                    except (TypeError, ValueError) as exc:
                        observation = {"ok": False, "data": [], "error": str(exc)}
                events.append({"event": "retrieval", "latency_ms": latency, "candidates": [(hit["document_id"], hit["chunk_id"], hit["score"]) for hit in observation["data"]]})
            elif name == "save_preference":
                if not isinstance(args, dict) or set(args) != {"key", "value"} or "i prefer" not in question.lower():
                    observation = {"ok": False, "data": None, "error": "INVALID_MEMORY_WRITE"}
                else:
                    try:
                        self.memory.set(user_id, args["key"], args["value"], f"direct user statement: {question}")
                        observation = {"ok": True, "data": {"key": args["key"]}, "error": None}
                    except ValueError as exc:
                        observation = {"ok": False, "data": None, "error": str(exc)}
                events.append({"event": "memory_write", "latency_ms": latency, "key": args.get("key") if isinstance(args, dict) else None, "ok": observation["ok"]})
            else:
                observation = {"ok": False, "data": None, "error": "UNKNOWN_TOOL"}
            call_id = response.get("id", f"call-{call_number}")
            messages.extend([
                {"role": "assistant", "content": None, "tool_calls": [{"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]},
                {"role": "tool", "name": name, "tool_call_id": call_id, "content": json.dumps(observation)},
            ])
        return {"status": "failed", "answer": "Model-call limit reached.", "citations": [], "events": events}


def build_agent(mock: bool, database: Path, docs: Path, trace: Path | None = None):
    if not list(docs.glob("*.md")):
        generate_documents(docs)
    index = BM25Index(ingest(docs))
    model: Model = MockModel() if mock else OpenAIModel(os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), os.getenv("OPENAI_API_KEY"))
    return KnowledgeAgent(model, index, MemoryStore(database), trace)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--db", type=Path, default=Path("memory.sqlite3"))
    parser.add_argument("--docs", type=Path, default=Path(__file__).parent / "data" / "docs")
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask"); ask.add_argument("question"); ask.add_argument("--user", required=True); ask.add_argument("--session", default="default")
    inspect = sub.add_parser("inspect"); inspect.add_argument("--user", required=True)
    forget = sub.add_parser("forget"); forget.add_argument("--user", required=True); forget.add_argument("--key")
    args = parser.parse_args(argv)
    agent = build_agent(args.mock or os.getenv("MOCK_LLM") == "1", args.db, args.docs, Path("trace.jsonl"))
    if args.command == "ask":
        print(json.dumps(agent.ask(args.user, args.session, args.question), indent=2))
    elif args.command == "inspect":
        print(json.dumps(agent.memory.list(args.user), indent=2))
    else:
        agent.memory.forget(args.user, args.key); print("Memory deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
