from __future__ import annotations

from backend.models import EvidenceResult, StructuredAnswer


class CitationValidator:
    def validate(self, answer: StructuredAnswer, evidence: list[EvidenceResult]) -> tuple[bool, list[str]]:
        if answer.insufficient_evidence:
            return True, []
        evidence_by_id = {item.chunk_id: item for item in evidence}
        problems: list[str] = []
        if not answer.sources:
            problems.append("Answer has no citations.")
        for source in answer.sources:
            chunk_id = str(source.get("chunk_id", ""))
            evidence_item = evidence_by_id.get(chunk_id)
            if evidence_item is None:
                problems.append(f"Citation chunk_id was not retrieved: {chunk_id}")
                continue
            expected = {
                "document": evidence_item.document,
                "source_filename": evidence_item.metadata.get("source_filename"),
                "section": evidence_item.section,
                "page": evidence_item.page,
            }
            for key, value in expected.items():
                if source.get(key) != value:
                    problems.append(f"Citation {chunk_id} has mismatched {key}.")
        return not problems, problems
