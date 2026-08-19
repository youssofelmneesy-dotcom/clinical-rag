from __future__ import annotations

import json
from pathlib import Path

from backend.config import CONFIDENCE_CONFIG_PATH
from backend.models import ConfidenceDecision, EvidenceResult


DEFAULT_THRESHOLD = 0.18


class ConfidenceGate:
    def __init__(self, threshold: float | None = None, config_path: Path = CONFIDENCE_CONFIG_PATH) -> None:
        self.threshold = threshold if threshold is not None else _load_threshold(config_path)

    def decide(self, evidence: list[EvidenceResult], question: str = "") -> ConfidenceDecision:
        confidence = max((item.similarity for item in evidence), default=0.0)
        ambiguity_reason = _clinical_ambiguity_reason(question)
        if ambiguity_reason:
            return ConfidenceDecision(False, confidence, self.threshold, ambiguity_reason)
        if confidence >= self.threshold:
            return ConfidenceDecision(True, confidence, self.threshold, "Best retrieved evidence met the calibrated threshold.")
        return ConfidenceDecision(False, confidence, self.threshold, "Retrieved evidence did not meet the calibrated threshold.")


def _load_threshold(config_path: Path) -> float:
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return float(data["selected_threshold"])
    return DEFAULT_THRESHOLD


def _clinical_ambiguity_reason(question: str) -> str | None:
    normalized = question.lower()
    patient_specific = any(term in normalized for term in ("my ", "this patient", "a patient", "specific patient", "for me"))
    missing_data = any(term in normalized for term in ("without", "missing", "no symptom", "no assessment", "no spirometry"))
    local_or_brand = any(term in normalized for term in ("brand", "local pharmacy", "dispense"))
    exact_prediction = any(term in normalized for term in ("precise", "guarantee", "life expectancy"))
    if local_or_brand:
        return "The question asks for local or product-specific advice not supported by retrieved guideline evidence."
    if patient_specific and missing_data:
        return "The question asks for individualized COPD advice but lacks required patient assessment details."
    if exact_prediction:
        return "The question asks for a precise individualized prediction that guideline retrieval cannot support."
    return None
