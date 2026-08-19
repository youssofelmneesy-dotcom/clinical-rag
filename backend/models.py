from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    document_name: str
    source_filename: str
    page: int
    section: str
    text: str
    subsection: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_type: str | None = None
    publication_date: str | None = None
    update_date: str | None = None
    jurisdiction: str | None = None

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        return {key: value for key, value in data.items() if value is not None}


@dataclass(frozen=True)
class EvidenceResult:
    chunk_id: str
    text: str
    distance: float
    similarity: float
    document: str
    page: int
    section: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScopeDecision:
    in_scope: bool
    reason: str
    signals: dict[str, Any]


@dataclass(frozen=True)
class ConfidenceDecision:
    sufficient: bool
    confidence: float
    threshold: float
    reason: str


@dataclass(frozen=True)
class StructuredAnswer:
    recommendation: str
    evidence: list[str]
    sources: list[dict[str, Any]]
    conflicting_guidance: list[str] = field(default_factory=list)
    insufficient_evidence: bool = False

    def render(self) -> str:
        if self.insufficient_evidence:
            return self.recommendation
        lines = ["Recommendation:", self.recommendation, "", "Evidence:"]
        lines.extend(f"- {item}" for item in self.evidence)
        if self.conflicting_guidance:
            lines.extend(["", "Conflicting Guidance:"])
            lines.extend(f"- {item}" for item in self.conflicting_guidance)
        lines.extend(["", "Sources:"])
        for source in self.sources:
            source_filename = source.get("source_filename") or source.get("filename")
            filename_part = f" | File: {source_filename}" if source_filename else ""
            lines.append(
                f"- Document: {source.get('document')}{filename_part} | Section: {source.get('section')} | Page: {source.get('page')} | Chunk: {source.get('chunk_id')}"
            )
        return "\n".join(lines)


@dataclass(frozen=True)
class ClaimVerificationResult:
    supported: bool
    supported_claims: list[str]
    unsupported_claims: list[str]
    reason: str
