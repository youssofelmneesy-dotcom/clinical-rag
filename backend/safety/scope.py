from __future__ import annotations

import re

from backend.models import EvidenceResult, ScopeDecision


COPD_TERMS = {
    "copd",
    "chronic obstructive pulmonary disease",
    "emphysema",
    "chronic bronchitis",
    "spirometry",
    "fev1",
    "fvc",
    "exacerbation",
    "bronchodilator",
    "pulmonary rehabilitation",
    "oxygen therapy",
    "smoking cessation",
    "inhaler",
    "dyspnoea",
    "dyspnea",
    "sputum",
}

OUT_OF_SCOPE_TERMS = {
    "appendicitis",
    "arthritis",
    "cancer",
    "chemotherapy",
    "colon",
    "diabetes",
    "hypertension",
    "asthma biologic",
    "myocardial infarction",
    "migraine",
    "insulin",
    "stroke",
    "cancer screening",
    "kidney failure",
    "kidney disease",
    "pregnancy",
    "rheumatoid",
}

COPD_CONTEXT_TERMS = {
    "diagnosis",
    "symptoms",
    "risk",
    "spirometry",
    "assessment",
    "severity",
    "stable",
    "management",
    "pharmacological",
    "non-pharmacological",
    "exacerbations",
    "oxygen",
    "rehabilitation",
    "smoking",
    "prognosis",
    "comorbidities",
    "prevention",
    "follow-up",
    "follow up",
}


class ScopeDetector:
    def decide(self, question: str, evidence: list[EvidenceResult] | None = None) -> ScopeDecision:
        normalized = question.lower()
        copd_hits = [term for term in COPD_TERMS if term in normalized]
        context_hits = [term for term in COPD_CONTEXT_TERMS if term in normalized]
        ood_hits = [term for term in OUT_OF_SCOPE_TERMS if term in normalized]
        unsafe_adjacent = ("cancer" in normalized and any(term in normalized for term in ("screening", "surveillance", "chemotherapy")))
        best_similarity = max((item.similarity for item in evidence or []), default=0.0)
        evidence_sections = {
            item.section
            for item in evidence or []
            if item.similarity > 0.2 and _has_copd_signal(item.text)
        }

        if unsafe_adjacent or (ood_hits and not copd_hits):
            return ScopeDecision(False, "Question is outside the supported COPD clinical scope.", {
                "copd_terms": copd_hits,
                "context_terms": context_hits,
                "out_of_scope_terms": ood_hits,
                "best_similarity": best_similarity,
            })
        if copd_hits or (context_hits and evidence_sections and best_similarity >= 0.45):
            return ScopeDecision(True, "Question matches COPD scope signals.", {
                "copd_terms": copd_hits,
                "context_terms": context_hits,
                "out_of_scope_terms": ood_hits,
                "best_similarity": best_similarity,
                "evidence_sections": sorted(evidence_sections),
            })
        return ScopeDecision(False, "No reliable COPD scope signal was found.", {
            "copd_terms": copd_hits,
            "context_terms": context_hits,
            "out_of_scope_terms": ood_hits,
            "best_similarity": best_similarity,
        })


def _has_copd_signal(text: str) -> bool:
    normalized = text.lower()
    return bool(re.search(r"\b(copd|chronic obstructive|spirometry|fev1|exacerbation)\b", normalized))
