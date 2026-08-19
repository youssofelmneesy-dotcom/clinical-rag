from __future__ import annotations

import re
from collections import Counter

from backend.models import ClaimVerificationResult, EvidenceResult, StructuredAnswer


STOPWORDS = {
    "the",
    "and",
    "or",
    "to",
    "of",
    "in",
    "for",
    "a",
    "an",
    "with",
    "that",
    "should",
    "be",
    "is",
    "are",
    "as",
    "by",
    "on",
    "from",
}


class ClaimVerifier:
    def verify(self, answer: StructuredAnswer, evidence: list[EvidenceResult]) -> ClaimVerificationResult:
        if answer.insufficient_evidence:
            return ClaimVerificationResult(True, [], [], "Refusal answers do not introduce clinical claims.")
        evidence_text = " ".join(item.text.lower() for item in evidence)
        claims = _extract_claims(answer)
        supported: list[str] = []
        unsupported: list[str] = []
        for claim in claims:
            if _claim_supported(claim, evidence_text):
                supported.append(claim)
            else:
                unsupported.append(claim)
        return ClaimVerificationResult(
            supported=not unsupported,
            supported_claims=supported,
            unsupported_claims=unsupported,
            reason="All extracted claims are lexically supported by retrieved evidence." if not unsupported else "Some extracted claims were not supported by retrieved evidence.",
        )


def _extract_claims(answer: StructuredAnswer) -> list[str]:
    text = " ".join([answer.recommendation, *answer.evidence, *answer.conflicting_guidance])
    claims = [item.strip() for item in re.split(r"(?<=[.!?])\s+|;\s+", text) if item.strip()]
    return [claim for claim in claims if len(_tokens(claim)) >= 4]


def _claim_supported(claim: str, evidence_text: str) -> bool:
    normalized_claim = _normalize(claim)
    normalized_evidence = _normalize(evidence_text)
    if normalized_claim in normalized_evidence:
        return True
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return True
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", claim)
    if any(number not in evidence_text for number in numbers):
        return False
    counts = Counter(claim_tokens)
    evidence_tokens = Counter(_tokens(evidence_text))
    matched = sum(min(count, evidence_tokens[token]) for token, count in counts.items())
    return matched / max(1, sum(counts.values())) >= 0.62


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9./%]+", " ", text.lower())).strip()


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS and len(token) > 2]
