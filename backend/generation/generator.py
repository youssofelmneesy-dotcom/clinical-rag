from __future__ import annotations

import os
import re
import json
from typing import Protocol

from backend.models import EvidenceResult, StructuredAnswer


REFUSAL = "I don't have sufficient evidence in the supported COPD guidelines to answer this question reliably."


class AnswerGenerator(Protocol):
    def generate(self, question: str, evidence: list[EvidenceResult]) -> StructuredAnswer:
        ...


class ExtractiveAnswerGenerator:
    def generate(self, question: str, evidence: list[EvidenceResult]) -> StructuredAnswer:
        if not evidence:
            return StructuredAnswer(recommendation=REFUSAL, evidence=[], sources=[], insufficient_evidence=True)
        selected = evidence[:3]
        snippets = [_best_sentence(item.text, question) for item in selected]
        recommendation = " ".join(snippet for snippet in snippets if snippet).strip()
        if not recommendation:
            recommendation = REFUSAL
            return StructuredAnswer(recommendation=recommendation, evidence=[], sources=[], insufficient_evidence=True)
        sources = [
            _source_from_evidence(item)
            for item in selected
        ]
        conflicts = _detect_potential_conflicts(selected)
        return StructuredAnswer(
            recommendation=recommendation,
            evidence=snippets,
            sources=sources,
            conflicting_guidance=conflicts,
        )


class OpenAIAnswerGenerator:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai is required for OpenAI generation. Install requirements.txt.") from exc
        self.client = OpenAI()

    def generate(self, question: str, evidence: list[EvidenceResult]) -> StructuredAnswer:
        prompt = _grounding_prompt(question, evidence)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are not the primary source of medical knowledge. "
                        "Use only the provided COPD guideline evidence. "
                        "If evidence is insufficient, refuse."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        text = response.choices[0].message.content or REFUSAL
        return _parse_structured_text(text, evidence)


def default_generator() -> AnswerGenerator:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIAnswerGenerator()
    return ExtractiveAnswerGenerator()


def _best_sentence(text: str, question: str) -> str:
    question_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    if not sentences:
        return text[:500].strip()
    return max(sentences, key=lambda sentence: len(question_terms.intersection(set(re.findall(r"[a-z0-9]+", sentence.lower())))))[:650]


def _grounding_prompt(question: str, evidence: list[EvidenceResult]) -> str:
    evidence_blocks = []
    for index, item in enumerate(evidence, start=1):
        evidence_blocks.append(
            f"[{index}] chunk_id: {item.chunk_id}\n"
            f"document: {item.document}\n"
            f"source_filename: {item.metadata.get('source_filename')}\n"
            f"section: {item.section}\n"
            f"page: {item.page}\n"
            f"text: {item.text}"
        )
    return (
        "Answer the COPD clinical question using only the evidence below. The evidence is the source of truth.\n"
        "Do not add any clinical claim, dose, duration, test threshold, or recommendation unless it is supported by the evidence.\n"
        "Keep GOLD and NICE separately attributable. If retrieved evidence conflicts, describe the conflict instead of merging it.\n"
        "If the evidence is insufficient, return insufficient_evidence=true and use the refusal message.\n"
        "Return valid JSON only with keys: recommendation, evidence, sources, conflicting_guidance, insufficient_evidence.\n"
        "Each source object must include document, source_filename, section, page, and chunk_id from the evidence.\n\n"
        f"Question: {question}\n\nEvidence:\n" + "\n\n".join(evidence_blocks)
    )


def _parse_structured_text(text: str, evidence: list[EvidenceResult]) -> StructuredAnswer:
    if "insufficient evidence" in text.lower():
        return StructuredAnswer(recommendation=REFUSAL, evidence=[], sources=[], insufficient_evidence=True)
    source_by_id = {item.chunk_id: _source_from_evidence(item) for item in evidence}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return _fallback_parse(text, evidence)
    if parsed.get("insufficient_evidence"):
        return StructuredAnswer(recommendation=REFUSAL, evidence=[], sources=[], insufficient_evidence=True)
    sources = []
    for source in parsed.get("sources", []):
        chunk_id = source.get("chunk_id")
        if chunk_id in source_by_id:
            sources.append(source_by_id[chunk_id])
    if not sources:
        sources = [_source_from_evidence(item) for item in evidence[:3]]
    return StructuredAnswer(
        recommendation=str(parsed.get("recommendation", ""))[:1500],
        evidence=[str(item) for item in parsed.get("evidence", [])][:6],
        sources=sources,
        conflicting_guidance=[str(item) for item in parsed.get("conflicting_guidance", [])][:4],
        insufficient_evidence=False,
    )


def _fallback_parse(text: str, evidence: list[EvidenceResult]) -> StructuredAnswer:
    sources = [_source_from_evidence(item) for item in evidence[:3]]
    lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
    recommendation = " ".join(line for line in lines if not line.lower().startswith(("evidence", "sources", "conflicting")))
    return StructuredAnswer(recommendation=recommendation[:1500], evidence=lines[:5], sources=sources)


def _source_from_evidence(item: EvidenceResult) -> dict[str, object]:
    return {
        "document": item.document,
        "source_filename": item.metadata.get("source_filename"),
        "section": item.section,
        "page": item.page,
        "chunk_id": item.chunk_id,
    }


def _detect_potential_conflicts(evidence: list[EvidenceResult]) -> list[str]:
    by_document: dict[str, list[str]] = {}
    for item in evidence:
        by_document.setdefault(item.document, []).append(item.text.lower())
    if len(by_document) < 2:
        return []
    combined = {document: " ".join(texts) for document, texts in by_document.items()}
    has_negative = any("not recommend" in text or "do not" in text for text in combined.values())
    has_positive = any("recommend" in text and "not recommend" not in text for text in combined.values())
    if has_negative and has_positive:
        return ["Retrieved GOLD and NICE evidence may differ; review the listed sources separately."]
    return []
