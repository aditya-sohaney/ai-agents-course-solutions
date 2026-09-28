"""Stateless, structured three-tool campus utility agent."""

from __future__ import annotations

import argparse
import ast
import json
import operator
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol


POLICY_PATH = Path(__file__).parent / "data" / "policies.json"
STATUSES = {"answered", "needs_clarification", "failed"}
FINAL_FIELDS = {"status", "answer", "tools_used", "error"}


def result(ok: bool, data: Any = None, error_code: str | None = None, message: str = ""):
    return {"ok": ok, "data": data, "error_code": error_code, "message": message}


def calculator(expression: str) -> dict[str, Any]:
    allowed = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
    try:
        if not isinstance(expression, str) or len(expression) > 100:
            raise ValueError("expression must be a string of at most 100 characters")
        tree = ast.parse(expression, mode="eval")

        def visit(node):
            if isinstance(node, ast.Expression):
                return visit(node.body)
            if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
                return float(node.value)
            if isinstance(node, ast.BinOp) and type(node.op) in allowed:
                return allowed[type(node.op)](visit(node.left), visit(node.right))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                return visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
            raise ValueError("unsupported arithmetic syntax")

        value = visit(tree)
        return result(True, int(value) if value.is_integer() else value, message="calculation complete")
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        return result(False, error_code="INVALID_EXPRESSION", message=str(exc))


CONVERSIONS = {
    ("miles", "kilometers"): 1.609344,
    ("kilometers", "miles"): 1 / 1.609344,
    ("meters", "feet"): 3.28084,
    ("feet", "meters"): 1 / 3.28084,
}


def convert_units(value: float, from_unit: str, to_unit: str) -> dict[str, Any]:
    if type(value) not in {int, float} or abs(value) > 1_000_000:
        return result(False, error_code="INVALID_VALUE", message="value must be a bounded number")
    key = (from_unit, to_unit)
    if key not in CONVERSIONS:
        return result(False, error_code="UNSUPPORTED_CONVERSION", message=f"cannot convert {from_unit} to {to_unit}")
    return result(True, round(value * CONVERSIONS[key], 4), message=f"converted to {to_unit}")


def lookup_policy(topic: str, path: Path = POLICY_PATH) -> dict[str, Any]:
    if not path.exists():
        return result(False, error_code="POLICY_DATA_UNAVAILABLE", message="policy data file is missing")
    policies = json.loads(path.read_text(encoding="utf-8"))
    normalized = topic.lower().strip().replace(" ", "_")
    if normalized in policies:
        return result(True, {"topic": normalized, "text": policies[normalized]}, message="policy found")
    matches = [key for key in policies if normalized in key or key in normalized]
    if len(matches) == 1:
        key = matches[0]
        return result(True, {"topic": key, "text": policies[key]}, message="policy found")
    return result(False, error_code="POLICY_NOT_FOUND", message="no matching fictional policy")


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform basic arithmetic.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_units",
            "description": "Convert supported distance units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number", "minimum": -1000000, "maximum": 1000000},
                    "from_unit": {"type": "string", "enum": ["miles", "kilometers", "meters", "feet"]},
                    "to_unit": {"type": "string", "enum": ["miles", "kilometers", "meters", "feet"]},
                },
                "required": ["value", "from_unit", "to_unit"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_policy",
            "description": "Look up one topic in the fictional campus policy file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["add_drop", "attendance", "bicycles", "exam_conflict", "food_lab", "guest_wifi", "library_hours", "quiet_hours"],
                    }
                },
                "required": ["topic"],
                "additionalProperties": False,
            },
        },
    },
]


def validate_final(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and set(payload) == FINAL_FIELDS
        and payload.get("status") in STATUSES
        and isinstance(payload.get("answer"), str)
        and isinstance(payload.get("tools_used"), list)
        and (payload.get("error") is None or isinstance(payload.get("error"), str))
    )


def validate_args(name: str, args: Any) -> str | None:
    if not isinstance(args, dict):
        return "arguments must be an object"
    expected = {
        "calculator": {"expression"},
        "convert_units": {"value", "from_unit", "to_unit"},
        "lookup_policy": {"topic"},
    }.get(name)
    if expected is None:
        return "unknown tool"
    if set(args) != expected:
        return f"expected fields: {sorted(expected)}"
    if name == "calculator" and not isinstance(args["expression"], str):
        return "expression must be a string"
    if name == "convert_units":
        if type(args["value"]) not in {int, float}:
            return "value must be a number"
        valid_units = {"miles", "kilometers", "meters", "feet"}
        if args["from_unit"] not in valid_units or args["to_unit"] not in valid_units:
            return "unit is outside the enum"
    if name == "lookup_policy" and not isinstance(args["topic"], str):
        return "topic must be a string"
    return None


class Model(Protocol):
    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


class MockModel:
    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        query = next(message["content"] for message in messages if message["role"] == "user")
        lowered = query.lower()
        used = [message.get("name") for message in messages if message["role"] == "tool"]
        observations = [json.loads(message["content"]) for message in messages if message["role"] == "tool"]

        if "convert" in lowered and not re.search(r"-?\d+(?:\.\d+)?", lowered):
            return {"type": "final", "payload": {"status": "needs_clarification", "answer": "What value should I convert?", "tools_used": used, "error": None}}
        if any(not observation["ok"] for observation in observations):
            error = next(observation for observation in observations if not observation["ok"])
            return {"type": "final", "payload": {"status": "failed", "answer": "I could not complete the request with verified tool data.", "tools_used": used, "error": error["error_code"]}}

        if any(word in lowered for word in ("calculate", "what is")) and "calculator" not in used:
            match = re.search(r"[-+*/().\d\s]{3,}", query)
            if match and any(op in match.group(0) for op in "+-*/"):
                return {"type": "tool", "id": "calc-1", "name": "calculator", "arguments": {"expression": match.group(0).strip().rstrip("?.")}}
        if "convert" in lowered and "convert_units" not in used:
            match = re.search(r"(-?\d+(?:\.\d+)?)\s*(miles|kilometers|meters|feet).*?\bto\s+(miles|kilometers|meters|feet)", lowered)
            if match:
                return {"type": "tool", "id": "convert-1", "name": "convert_units", "arguments": {"value": float(match.group(1)), "from_unit": match.group(2), "to_unit": match.group(3)}}
        policy_topics = {
            "quiet": "quiet_hours", "library": "library_hours", "wifi": "guest_wifi",
            "exam": "exam_conflict", "bicycle": "bicycles", "lab food": "food_lab",
            "attendance": "attendance", "drop": "add_drop",
        }
        if "lookup_policy" not in used:
            for phrase, topic in policy_topics.items():
                if phrase in lowered:
                    return {"type": "tool", "id": "policy-1", "name": "lookup_policy", "arguments": {"topic": topic}}

        if observations:
            summaries = [str(observation["data"]) for observation in observations]
            answer = "; ".join(summaries)
        else:
            answer = "I can calculate, convert supported distance units, or look up a fictional campus policy."
        return {"type": "final", "payload": {"status": "answered", "answer": answer, "tools_used": used, "error": None}}


class OpenAIModel:
    def __init__(self, model: str, api_key: str | None):
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def respond(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            response_format={"type": "json_object"},
            max_tokens=350,
        )
        message = response.choices[0].message
        if message.tool_calls:
            call = message.tool_calls[0]
            try:
                arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                arguments = None
            return {"type": "tool", "id": call.id, "name": call.function.name, "arguments": arguments}
        try:
            return {"type": "final", "payload": json.loads(message.content or "{}")}
        except json.JSONDecodeError:
            return {"type": "final", "payload": None}


@dataclass(frozen=True)
class TraceEvent:
    request_id: str
    event_type: str
    tool_name: str | None
    latency_ms: float
    success: bool
    error_code: str | None


class CampusAgent:
    def __init__(self, model: Model, trace_path: Path | None = None):
        self.model = model
        self.trace_path = trace_path

    def _emit(self, event: TraceEvent):
        if self.trace_path:
            with self.trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")

    def _dispatch(self, name: str, args: Any, fail_tool: str | None):
        validation_error = validate_args(name, args)
        if validation_error:
            return result(False, error_code="INVALID_ARGUMENTS", message=validation_error)
        if name == fail_tool:
            return result(False, error_code="TOOL_UNAVAILABLE", message="controlled failure")
        return {
            "calculator": lambda: calculator(**args),
            "convert_units": lambda: convert_units(**args),
            "lookup_policy": lambda: lookup_policy(**args),
        }[name]()

    def run(self, query: str, fail_tool: str | None = None) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "Use only verified tool results. Return JSON fields status, answer, tools_used, error."},
            {"role": "user", "content": query},
        ]
        calls_seen: set[str] = set()
        tool_count = 0
        repair_used = False
        for _ in range(5):
            started = time.perf_counter()
            response = self.model.respond(messages)
            latency = (time.perf_counter() - started) * 1000
            if response.get("type") == "final":
                payload = response.get("payload")
                if validate_final(payload):
                    self._emit(TraceEvent(request_id, "final", None, latency, True, None))
                    return payload
                if not repair_used:
                    repair_used = True
                    messages.append({"role": "system", "content": "Repair the final object to the exact required schema."})
                    continue
                return {"status": "failed", "answer": "The model returned an invalid final object.", "tools_used": [], "error": "INVALID_FINAL_SCHEMA"}

            name, args = response.get("name"), response.get("arguments")
            signature = json.dumps([name, args], sort_keys=True)
            if signature in calls_seen:
                return {"status": "failed", "answer": "A repeated tool call was stopped.", "tools_used": [], "error": "REPEATED_CALL"}
            if tool_count >= 3:
                return {"status": "failed", "answer": "The tool limit was reached.", "tools_used": [], "error": "TOOL_LIMIT"}
            calls_seen.add(signature)
            tool_count += 1
            observation = self._dispatch(name, args, fail_tool)
            self._emit(TraceEvent(request_id, "tool", name, latency, observation["ok"], observation["error_code"]))
            call_id = response.get("id", f"call-{tool_count}")
            messages.extend([
                {"role": "assistant", "content": None, "tool_calls": [{"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]},
                {"role": "tool", "name": name, "tool_call_id": call_id, "content": json.dumps(observation)},
            ])
        return {"status": "failed", "answer": "The model-call limit was reached.", "tools_used": [], "error": "MODEL_LIMIT"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--fail-tool", choices=["calculator", "convert_units", "lookup_policy"])
    parser.add_argument("--trace", type=Path, default=Path("trace.jsonl"))
    args = parser.parse_args(argv)
    model = MockModel() if args.mock or os.getenv("MOCK_LLM") == "1" else OpenAIModel(os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), os.getenv("OPENAI_API_KEY"))
    print(json.dumps(CampusAgent(model, args.trace).run(args.query, args.fail_tool), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

