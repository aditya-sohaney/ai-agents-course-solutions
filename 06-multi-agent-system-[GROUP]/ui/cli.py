from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from contracts import ResearchRequest
from orchestration.runner import ResearchOrchestrator


def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("question"); parser.add_argument("--mock", action="store_true"); parser.add_argument("--inject", choices=["timeout", "malformed", "empty"]); parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    brief = ResearchOrchestrator(Path("trace.jsonl")).run(ResearchRequest(args.question), args.inject)
    if args.output: args.output.write_text(brief.markdown, encoding="utf-8")
    print(brief.markdown); print(f"\nstatus={brief.status} stop={brief.stop_reason} citations={len(brief.citations)}")
    return 0


if __name__ == "__main__": raise SystemExit(main())

