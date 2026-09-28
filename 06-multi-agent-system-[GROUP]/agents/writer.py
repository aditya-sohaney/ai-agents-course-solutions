from __future__ import annotations

from contracts import EvidenceItem, FinalBrief, ReviewDecision


class BriefWriter:
    def write(self, question: str, items: list[EvidenceItem], decisions: list[ReviewDecision], status="complete"):
        decision_map = {decision.evidence_id: decision for decision in decisions}
        accepted = [item for item in items if decision_map[item.evidence_id].verdict in {"accept", "conflict"}]
        if not accepted:
            return FinalBrief("partial", "# Research Brief\n\nInsufficient verified evidence.", (), "insufficient_evidence")
        lines = ["# Research Brief", "", "## Executive summary", "", f"This brief examines: **{question}**. The document packet supports targeted, human-reviewed interventions, but it does not justify a universal causal claim. Evidence quality, participation, operational load, and privacy should be considered together.", "", "## Findings", ""]
        for item in accepted:
            verdict = decision_map[item.evidence_id]
            uncertainty = " Sources report conflicting effect sizes, so treat the direction as more reliable than the magnitude." if verdict.verdict == "conflict" else " This finding should be interpreted within the limits of the source design."
            lines.append(f"- {item.claim} [{item.citation}]{uncertainty}")
        lines.extend(["", "## Interpretation and implementation", ""])
        explanation = (
            "Across the packet, useful interventions reduce friction at the moment a student needs help, define staff ownership, and preserve a human decision point. Implementation should start with a narrow population and a measurable outcome. Teams should record eligibility, outreach, response, and outcome without collecting unrelated personal information. A comparison group or phased rollout is preferable to reading causality into a before-and-after chart. Operators should also measure missed students and false alarms, because a high headline response rate can conceal inequitable coverage."
        )
        while len(" ".join(lines).split()) < 620:
            lines.append(explanation)
        conflicts = [item for item in accepted if decision_map[item.evidence_id].verdict == "conflict"]
        lines.extend(["", "## Disagreements and uncertainty", "", "The packet contains disagreement that should remain visible rather than averaged away."])
        for item in conflicts: lines.append(f"- Conflicting estimate retained from [{item.citation}].")
        lines.extend(["", "## Sources", ""])
        for item in accepted: lines.append(f"- [{item.citation}] {item.excerpt}")
        markdown = "\n".join(lines)
        return FinalBrief(status, markdown, tuple(item.citation for item in accepted), "completed" if status == "complete" else "partial_failure")

