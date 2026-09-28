from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from agent import CalculatorAgent, MockModel, calculate  # noqa: E402


def test_addition_and_precedence():
    assert calculate("2 + 3 * 4")["result"] == 14


def test_parentheses():
    assert calculate("(17 * 4) + 9")["result"] == 77


def test_decimals_and_division():
    assert calculate("7.5 / 2")["result"] == 3.75


def test_unary_minus():
    assert calculate("-4 + 10")["result"] == 6


def test_rejects_code_execution():
    result = calculate("__import__('os').system('echo unsafe')")
    assert not result["ok"]
    assert result["result"] is None


def test_rejects_division_by_zero():
    assert not calculate("10 / 0")["ok"]


def test_agent_returns_observation_before_final_answer():
    model = MockModel()
    result = CalculatorAgent(model).run("What is (17 * 4) + 9?")
    assert result.status == "answered"
    assert result.answer == "The answer is 77."
    assert result.trace[0].event == "tool_call"
    assert result.trace[0].observation == {"ok": True, "result": 77, "error": None}
    assert result.trace[-1].stop_reason == "model_answer"


def test_non_arithmetic_question_skips_tool():
    result = CalculatorAgent(MockModel()).run("What is a confidence interval?")
    assert result.status == "answered"
    assert all(event.event != "tool_call" for event in result.trace)


class RepeatingModel:
    def respond(self, messages):
        return {
            "type": "tool",
            "id": "repeat",
            "name": "calculator",
            "arguments": {"expression": "1 + 1"},
        }


def test_loop_stops_after_three_calls():
    result = CalculatorAgent(RepeatingModel()).run("loop")
    assert result.status == "failed"
    assert len([event for event in result.trace if event.event == "tool_call"]) == 3
    assert result.trace[-1].stop_reason == "limit"

