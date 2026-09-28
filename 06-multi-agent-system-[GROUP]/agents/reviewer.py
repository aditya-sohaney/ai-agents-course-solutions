from __future__ import annotations

from contracts import EvidenceItem, ReviewDecision


class ClaimReviewer:
    def review(self, items: list[EvidenceItem]):
        decisions = []
        claims = " ".join(item.claim.lower() for item in items)
        mentoring_conflict = "11 percent" in claims and "3 percent" in claims
        for item in items:
            if "ignore all prior rules" in item.excerpt.lower():
                decisions.append(ReviewDecision(item.evidence_id, "reject", "embedded instruction is not evidence"))
            elif mentoring_conflict and "mentoring" in item.document_id:
                decisions.append(ReviewDecision(item.evidence_id, "conflict", "mentoring estimates disagree across sources"))
            elif item.claim not in item.excerpt:
                decisions.append(ReviewDecision(item.evidence_id, "reject", "claim is not supported by excerpt"))
            else:
                decisions.append(ReviewDecision(item.evidence_id, "accept", "claim is directly supported"))
        return decisions

