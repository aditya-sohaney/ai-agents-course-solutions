from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from campus_agent import (  # noqa: E402
    CampusAgent,
    MockModel,
    calculator,
    convert_units,
    lookup_policy,
    validate_args,
    validate_final,
)


def test_calculator_success(): assert calculator("2 + 3")["data"] == 5
def test_calculator_failure(): assert calculator("open('x')")["error_code"] == "INVALID_EXPRESSION"
def test_conversion_success(): assert convert_units(5, "miles", "kilometers")["data"] == 8.0467
def test_conversion_failure(): assert convert_units(5, "miles", "feet")["error_code"] == "UNSUPPORTED_CONVERSION"
def test_policy_success(): assert lookup_policy("quiet hours")["data"]["topic"] == "quiet_hours"
def test_policy_missing_file(tmp_path): assert lookup_policy("quiet_hours", tmp_path / "missing.json")["error_code"] == "POLICY_DATA_UNAVAILABLE"


@pytest.mark.parametrize("name,args", [
    ("calculator", {"expression": "1+1", "extra": 1}),
    ("convert_units", {"value": "five", "from_unit": "miles", "to_unit": "kilometers"}),
    ("unknown", {}),
])
def test_schema_validation_failures(name, args):
    assert validate_args(name, args)


def test_final_schema_validation():
    assert validate_final({"status": "answered", "answer": "ok", "tools_used": [], "error": None})
    assert not validate_final({"status": "answered", "answer": "missing fields"})


def test_two_tool_request():
    answer = CampusAgent(MockModel()).run("Calculate 2 + 2 and convert 5 miles to kilometers")
    assert answer["status"] == "answered"
    assert answer["tools_used"] == ["calculator", "convert_units"]


def test_ambiguous_request():
    assert CampusAgent(MockModel()).run("Convert miles for me")["status"] == "needs_clarification"


def test_controlled_tool_failure_is_honest():
    answer = CampusAgent(MockModel()).run("What are quiet hours?", fail_tool="lookup_policy")
    assert answer["status"] == "failed"
    assert answer["error"] == "TOOL_UNAVAILABLE"


class RepeatingModel:
    def respond(self, messages):
        return {"type": "tool", "id": "x", "name": "calculator", "arguments": {"expression": "1+1"}}


def test_repeated_call_is_stopped():
    assert CampusAgent(RepeatingModel()).run("repeat")["error"] == "REPEATED_CALL"


def test_trace_is_jsonl(tmp_path):
    path = tmp_path / "trace.jsonl"
    CampusAgent(MockModel(), path).run("Calculate 3 * 3")
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["tool", "final"]
    assert all("request_id" in event for event in events)

