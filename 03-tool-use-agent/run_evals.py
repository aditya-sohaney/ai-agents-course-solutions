import json
from pathlib import Path

from campus_agent import CampusAgent, MockModel


def main():
    cases = [json.loads(line) for line in (Path(__file__).parent / "evals" / "acceptance.jsonl").read_text().splitlines() if line]
    passed = 0
    for case in cases:
        actual = CampusAgent(MockModel()).run(case["input"], case.get("fail_tool"))
        ok = actual["status"] == case["expected_status"] and all(tool in actual["tools_used"] for tool in case["required_tools"])
        passed += ok
        print(json.dumps({"id": case["id"], "passed": ok, "actual": actual}, sort_keys=True))
    print(f"summary: {passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())

