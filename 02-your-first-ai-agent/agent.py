"""One explicit agent loop with one safe calculator tool."""

from __future__ import annotations

import argparse
import ast
import json
import operator
import os
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Protocol


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate basic arithmetic using +, -, *, / and parentheses.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
}


class CalculatorError(ValueError):
    pass


_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculate(expression: str) -> dict[str, Any]:
    """Safely evaluate the exact arithmetic subset promised by the schema."""
    try:
        if not isinstance(expression, str) or not expression.strip():
            raise CalculatorError("expression must be a non-empty string")
        if len(expression) > 100:
            raise CalculatorError("expression is too long")
        tree = ast.parse(expression, mode="eval")

        def visit(node: ast.AST, depth: int = 0) -> float:
            if depth > 20:
                raise CalculatorError("expression is too deeply nested")
            if isinstance(node, ast.Expression):
                return visit(node.body, depth + 1)
            if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
                return float(node.value)
            if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
                left = visit(node.left, depth + 1)
                right = visit(node.right, depth + 1)
                value = _BINARY[type(node.op)](left, right)
                if abs(value) > 1e12:
                    raise CalculatorError("result exceeds the allowed magnitude")
                return value
            if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
                return _UNARY[type(node.op)](visit(node.operand, depth + 1))
            raise CalculatorError(f"unsupported syntax: {type(node).__name__}")

        value = visit(tree)
        if value.is_integer():
            value = int(value)
        return {"ok": True, "result": value, "error": None}
    except (SyntaxError, ZeroDivisionError, CalculatorError) as exc:
        return {"ok": False, "result": None, "error": str(exc)}


@dataclass(frozen=True)
class TraceEvent:
    iteration: int
    event: str
    tool: str | None
    arguments: dict[str, Any] | None
    observation: dict[str, Any] | None
    stop_reason: str | None
    latency_ms: float


@dataclass(frozen=True)
class AgentResult:
    answer: str
    status: str
    trace: list[TraceEvent]


class Model(Protocol):
    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


class MockModel:
    """A deterministic model double that still exercises the real loop."""

    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        last = messages[-1]
        if last["role"] == "tool":
            observation = json.loads(last["content"])
            if observation["ok"]:
                return {"type": "final", "content": f"The answer is {observation['result']}."}
            return {
                "type": "final",
                "content": f"I could not calculate that safely: {observation['error']}",
            }
        prompt = last["content"]
        lowered = prompt.lower()
        arithmetic = re.search(r"[-+*/().\d\s]{3,}", prompt)
        if arithmetic and any(character in arithmetic.group(0) for character in "+-*/"):
            expression = arithmetic.group(0).strip().rstrip("?.")
            return {
                "type": "tool",
                "id": "mock-call-1",
                "name": "calculator",
                "arguments": {"expression": expression},
            }
        if "__import__" in lowered or "unsupported" in lowered:
            return {
                "type": "tool",
                "id": "mock-call-1",
                "name": "calculator",
                "arguments": {"expression": "__import__('os').system('echo no')"},
            }
        return {"type": "final", "content": "That question does not require the calculator."}


class OpenAIModel:
    def __init__(self, model: str, api_key: str | None) -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=[TOOL_SCHEMA],
            tool_choice="auto",
            max_tokens=250,
        )
        message = response.choices[0].message
        if message.tool_calls:
            call = message.tool_calls[0]
            try:
                arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                arguments = {"_malformed": call.function.arguments}
            return {
                "type": "tool",
                "id": call.id,
                "name": call.function.name,
                "arguments": arguments,
            }
        return {"type": "final", "content": message.content or ""}


class CalculatorAgent:
    def __init__(self, model: Model, max_model_calls: int = 3) -> None:
        self.model = model
        self.max_model_calls = max_model_calls

    def run(self, question: str) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Use the calculator for arithmetic. Its observation is authoritative. "
                    "Never invent a calculation result."
                ),
            },
            {"role": "user", "content": question},
        ]
        trace: list[TraceEvent] = []
        for iteration in range(1, self.max_model_calls + 1):
            started = time.perf_counter()
            response = self.model.respond(messages)
            latency_ms = (time.perf_counter() - started) * 1000
            if response.get("type") == "final":
                trace.append(
                    TraceEvent(iteration, "final", None, None, None, "model_answer", latency_ms)
                )
                return AgentResult(response.get("content", ""), "answered", trace)

            name = response.get("name")
            arguments = response.get("arguments")
            if name != "calculator":
                observation = {"ok": False, "result": None, "error": "unknown tool"}
            elif not isinstance(arguments, dict) or set(arguments) != {"expression"}:
                observation = {
                    "ok": False,
                    "result": None,
                    "error": "arguments must contain only expression",
                }
            else:
                observation = calculate(arguments["expression"])
            trace.append(
                TraceEvent(
                    iteration,
                    "tool_call",
                    name,
                    arguments if isinstance(arguments, dict) else None,
                    observation,
                    None,
                    latency_ms,
                )
            )
            call_id = response.get("id", f"call-{iteration}")
            messages.extend(
                [
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(arguments),
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(observation),
                    },
                ]
            )
        trace.append(TraceEvent(self.max_model_calls, "stop", None, None, None, "limit", 0))
        return AgentResult("I could not finish within the three-call limit.", "failed", trace)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args(argv)
    use_mock = args.mock or os.getenv("MOCK_LLM") == "1"
    try:
        model: Model = (
            MockModel()
            if use_mock
            else OpenAIModel(
                os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), os.getenv("OPENAI_API_KEY")
            )
        )
        result = CalculatorAgent(model).run(args.question)
    except Exception as exc:
        print(f"Agent could not start: {type(exc).__name__}: {exc}")
        return 2
    for event in result.trace:
        print(json.dumps(asdict(event), sort_keys=True))
    print(f"Response: {result.answer}")
    return 0 if result.status == "answered" else 1


if __name__ == "__main__":
    raise SystemExit(main())

