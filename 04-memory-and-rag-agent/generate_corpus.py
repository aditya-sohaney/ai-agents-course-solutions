"""Generate a deterministic synthetic document collection of at least 6,000 words."""

from __future__ import annotations

import argparse
from pathlib import Path


TOPICS = {
    "quiet_spaces": {
        "title": "Quiet Spaces Handbook",
        "fact": "Residence quiet hours begin at 10 p.m. Sunday through Thursday and midnight on Friday and Saturday.",
        "keywords": "quiet residence noise study sleep courtesy hall coordinator",
    },
    "aid_deadlines": {
        "title": "Student Aid Calendar",
        "fact": "The priority financial aid application deadline is March 1, and complete files receive review first.",
        "keywords": "aid deadline application grant scholarship verification finance",
    },
    "lab_safety": {
        "title": "Teaching Laboratory Safety Guide",
        "fact": "Students must wear splash goggles whenever chemicals or heated glassware are in use.",
        "keywords": "laboratory safety goggles chemical glassware incident supervisor",
    },
    "transit_guide": {
        "title": "Campus Transit Guide",
        "fact": "The Blue Loop shuttle runs every fifteen minutes from 7 a.m. until 11 p.m. on weekdays.",
        "keywords": "transit shuttle blue loop stop route accessible weekday",
    },
    "wellness_services": {
        "title": "Student Wellness Services",
        "fact": "Students may schedule up to six short-term counseling visits each academic year at no charge.",
        "keywords": "wellness counseling appointment urgent health privacy support",
    },
    "research_ethics": {
        "title": "Undergraduate Research Ethics Manual",
        "fact": "Research involving living people requires ethics review before recruitment or data collection begins.",
        "keywords": "research ethics participant consent review data protocol recruitment",
    },
}


def generate_documents(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for doc_id, item in TOPICS.items():
        sections = [f"# {item['title']}", "", item["fact"], ""]
        for number in range(1, 25):
            sections.extend(
                [
                    f"## Scenario {number}: applying the guidance",
                    "",
                    (
                        f"This fictional scenario explains {item['keywords']} in a routine campus setting. "
                        f"The controlling guidance remains: {item['fact']} Staff document the question, "
                        "identify the relevant handbook section, explain the reason in plain language, and "
                        "record any exception instead of inventing one. Students should ask the named campus "
                        "office when facts are incomplete. The example is educational, uses no personal data, "
                        "and exists so retrieval can distinguish a supported answer from a plausible guess. "
                        f"Scenario identifier {doc_id}-{number} makes this passage stable across regenerations."
                    ),
                    "",
                    (
                        "A careful response quotes only the minimum relevant rule, preserves uncertainty, and "
                        "points back to this handbook. Related words are repeated deliberately for a transparent "
                        "lexical retrieval exercise. Conflicting or absent guidance must be surfaced rather than "
                        "resolved through general model knowledge."
                    ),
                    "",
                ]
            )
        path = output_dir / f"{doc_id}.md"
        path.write_text("\n".join(sections), encoding="utf-8")
        paths.append(path)
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "docs")
    args = parser.parse_args(argv)
    paths = generate_documents(args.output)
    words = sum(len(path.read_text(encoding="utf-8").split()) for path in paths)
    print(f"generated {len(paths)} documents with {words} words")
    return 0 if len(paths) >= 6 and words >= 6000 else 1


if __name__ == "__main__":
    raise SystemExit(main())

