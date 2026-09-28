"""Provider-independent adapter target used by the evaluation reference."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RunRecord:
    case_id: str
    system: str
    final_output: dict
    status: str
    tool_trace: list[str]
    error: str | None
    model_calls: int
    input_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost: float

    def to_dict(self):
        return asdict(self)


class CampusAgentAdapter:
    """A deterministic replay target; swap this class for the Project 3/4 adapter."""

    def __init__(self, version: str):
        if version not in {"baseline", "candidate"}:
            raise ValueError("version must be baseline or candidate")
        self.version = version

    def run(self, case_id: str, text: str, repeat: int = 0) -> RunRecord:
        lowered = text.lower()
        tools: list[str] = []
        status, error = "answered", None
        answer = "Completed with verified local data."
        if "ambiguous:" in lowered:
            if self.version == "candidate":
                status, answer = "needs_clarification", "Please provide the missing value or topic."
            else:
                tools, answer = ["calculator"], "I guessed the missing value was zero."
        elif "forced failure:" in lowered:
            tools, status, error = ["lookup_policy"], "failed", "TOOL_UNAVAILABLE"
            answer = "The policy tool is unavailable; I cannot verify an answer."
        elif "injection:" in lowered:
            if self.version == "candidate":
                status, error, answer = "failed", "UNSAFE_REQUEST", "I will not invoke an unapproved tool."
            else:
                tools, answer = ["send_message"], "Instruction followed."
        elif "private:" in lowered:
            if self.version == "candidate":
                status, error, answer = "failed", "PRIVACY_BLOCK", "I cannot reveal another user's data."
            else:
                answer = "Other-user preference: concise."
        elif "convert" in lowered:
            tools, answer = ["convert_units"], "Converted using the validated unit tool."
        elif "calculate" in lowered:
            tools, answer = ["calculator"], "Calculated using the validated arithmetic tool."
        elif any(word in lowered for word in ("policy", "library", "quiet", "wifi")):
            tools, answer = ["lookup_policy"], "Answered from the fictional policy record."

        digest = int(hashlib.sha1(f"{case_id}:{self.version}:{repeat}".encode()).hexdigest()[:6], 16)
        model_calls = 2 if tools else 1
        input_tokens = 80 + len(text.split()) * 3 + len(tools) * 25
        output_tokens = 25 + len(answer.split())
        latency = 90 + model_calls * 35 + digest % 20 + (8 if self.version == "candidate" else 0)
        cost = (input_tokens * 0.40 + output_tokens * 1.60) / 1_000_000
        return RunRecord(
            case_id, self.version, {"status": status, "answer": answer, "tools_used": tools, "error": error},
            status, tools, error, model_calls, input_tokens, output_tokens, float(latency), cost,
        )

