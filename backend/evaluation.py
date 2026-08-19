from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from backend.config import CONFIDENCE_CONFIG_PATH, EVALUATION_REPORT_PATH, RetrievalConfig
from backend.models import EvidenceResult
from backend.retrieval.retriever import Retriever


@dataclass(frozen=True)
class EvaluationRecord:
    question: str
    category: str
    answerable: bool
    expected_document: str | None = None
    expected_section_terms: list[str] | None = None
    expected_terms: list[str] | None = None
    expected_page: int | None = None


def load_evaluation_dataset(path: Path) -> list[EvaluationRecord]:
    records: list[EvaluationRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(EvaluationRecord(**json.loads(line)))
    return records


def evaluate_retrieval(
    records: list[EvaluationRecord],
    retriever: Retriever,
    k: int = RetrievalConfig.default_k,
) -> dict[str, Any]:
    rows = []
    precisions: list[float] = []
    recalls: list[float] = []
    hit_rates: list[float] = []
    answerable_rows = [record for record in records if record.answerable]
    for record in records:
        evidence = retriever.retrieve(record.question, k=k)
        relevance = [_is_relevant(record, item) for item in evidence]
        relevant_count = sum(relevance)
        precision = relevant_count / k if record.answerable else 0.0
        recall = 1.0 if record.answerable and relevant_count > 0 else 0.0
        hit = 1.0 if relevant_count > 0 else 0.0
        if record.answerable:
            precisions.append(precision)
            recalls.append(recall)
            hit_rates.append(hit)
        rows.append(
            {
                "question": record.question,
                "category": record.category,
                "answerable": record.answerable,
                "expected_document": record.expected_document,
                "expected_terms": record.expected_terms,
                "top_results": [_result_row(item, relevance[index]) for index, item in enumerate(evidence)],
                "precision_at_k": precision,
                "recall_at_k": recall,
                "hit": hit,
                "best_similarity": max((item.similarity for item in evidence), default=0.0),
            }
        )
    thresholds = _evaluate_thresholds(rows)
    return {
        "k": k,
        "record_count": len(records),
        "answerable_count": len(answerable_rows),
        "precision_at_k": mean(precisions) if precisions else 0.0,
        "recall_at_k": mean(recalls) if recalls else 0.0,
        "hit_rate_at_k": mean(hit_rates) if hit_rates else 0.0,
        "threshold_analysis": thresholds,
        "rows": rows,
    }


def evaluate_multiple_k(records: list[EvaluationRecord], retriever: Retriever, values: tuple[int, ...] = (3, 5, 10)) -> dict[str, Any]:
    return {f"k_{k}": evaluate_retrieval(records, retriever, k=k) for k in values}


def write_evaluation_report(report: dict[str, Any], report_path: Path = EVALUATION_REPORT_PATH) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    selected = report["threshold_analysis"]["selected"]
    with CONFIDENCE_CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(selected, handle, indent=2)


def _is_relevant(record: EvaluationRecord, item: EvidenceResult) -> bool:
    if not record.answerable:
        return False
    document_match = not record.expected_document or item.metadata.get("document_id") == record.expected_document
    text = f"{item.section} {item.text}".lower()
    section_terms = record.expected_section_terms or []
    evidence_terms = record.expected_terms or []
    section_match = not section_terms or any(term.lower() in text for term in section_terms)
    terms_match = not evidence_terms or any(term.lower() in text for term in evidence_terms)
    page_match = record.expected_page is None or abs(item.page - record.expected_page) <= 2
    return document_match and section_match and terms_match and page_match


def _result_row(item: EvidenceResult, relevant: bool) -> dict[str, Any]:
    return {
        "chunk_id": item.chunk_id,
        "document": item.document,
        "document_id": item.metadata.get("document_id"),
        "page": item.page,
        "section": item.section,
        "distance": item.distance,
        "similarity": item.similarity,
        "relevant": relevant,
        "text_preview": item.text[:300],
    }


def _evaluate_thresholds(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [round(value / 100, 2) for value in range(5, 61, 5)]
    analyses = []
    for threshold in candidates:
        false_accepts = 0
        false_rejects = 0
        true_accepts = 0
        true_rejects = 0
        for row in rows:
            accepted = row["best_similarity"] >= threshold
            should_accept = bool(row["answerable"] and row["hit"])
            if accepted and should_accept:
                true_accepts += 1
            elif accepted and not should_accept:
                false_accepts += 1
            elif not accepted and should_accept:
                false_rejects += 1
            else:
                true_rejects += 1
        analyses.append(
            {
                "selected_threshold": threshold,
                "true_accepts": true_accepts,
                "false_accepts": false_accepts,
                "false_rejects": false_rejects,
                "true_rejects": true_rejects,
                "error_count": false_accepts + false_rejects,
            }
        )
    selected = min(analyses, key=lambda item: (item["false_accepts"], item["error_count"], -item["true_accepts"]))
    return {"candidates": analyses, "selected": selected}
