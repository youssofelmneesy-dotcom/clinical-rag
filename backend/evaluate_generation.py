from __future__ import annotations

import json

from backend.config import EVALUATION_DATASET_PATH, EVALUATION_DIR
from backend.evaluation import load_evaluation_dataset
from backend.pipeline import ClinicalRagPipeline


GENERATION_REPORT_PATH = EVALUATION_DIR / "generation_safety_report.json"


def evaluate_generation() -> dict:
    pipeline = ClinicalRagPipeline()
    records = load_evaluation_dataset(EVALUATION_DATASET_PATH)
    rows = []
    for record in records:
        response = pipeline.answer(record.question)
        refused = response.answer.insufficient_evidence or "outside the supported COPD clinical scope" in response.final_text
        should_refuse = not record.answerable
        citation_traceable = response.answer.insufficient_evidence or all(
            source.get("chunk_id") in {item.chunk_id for item in response.evidence}
            for source in response.answer.sources
        )
        rows.append(
            {
                "question": record.question,
                "category": record.category,
                "answerable": record.answerable,
                "refused": refused,
                "should_refuse": should_refuse,
                "refusal_correct": refused == should_refuse,
                "confidence": response.confidence.confidence,
                "threshold": response.confidence.threshold,
                "in_scope": response.scope.in_scope,
                "claim_verification_supported": response.verification.supported,
                "citation_traceable": citation_traceable,
            }
        )
    report = {
        "record_count": len(rows),
        "refusal_accuracy": _rate(row["refusal_correct"] for row in rows),
        "citation_traceability_rate": _rate(row["citation_traceable"] for row in rows),
        "claim_verification_pass_rate": _rate(row["claim_verification_supported"] for row in rows),
        "unsupported_claim_failures": [
            row for row in rows if row["answerable"] and not row["claim_verification_supported"]
        ],
        "rows": rows,
    }
    with GENERATION_REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


def _rate(values) -> float:
    values = list(values)
    return sum(bool(value) for value in values) / max(1, len(values))


def main() -> None:
    report = evaluate_generation()
    print(f"Evaluated {report['record_count']} generation/safety cases")
    print(f"Refusal accuracy: {report['refusal_accuracy']:.3f}")
    print(f"Citation traceability: {report['citation_traceability_rate']:.3f}")
    print(f"Claim verification pass rate: {report['claim_verification_pass_rate']:.3f}")


if __name__ == "__main__":
    main()
