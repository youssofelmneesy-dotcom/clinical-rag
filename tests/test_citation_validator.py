from backend.models import EvidenceResult, StructuredAnswer
from backend.safety.citation_validator import CitationValidator


def evidence():
    return [
        EvidenceResult(
            "gold-2026:abc",
            "COPD diagnosis requires post-bronchodilator spirometry.",
            0.1,
            0.9,
            "GOLD 2026 Global Strategy Report",
            38,
            "SPIROMETRY",
            {
                "document_id": "gold-2026",
                "source_filename": "GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf",
            },
        )
    ]


def test_citation_validator_accepts_retrieved_exact_metadata():
    answer = StructuredAnswer(
        "COPD diagnosis requires post-bronchodilator spirometry.",
        ["COPD diagnosis requires post-bronchodilator spirometry."],
        [
            {
                "document": "GOLD 2026 Global Strategy Report",
                "source_filename": "GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf",
                "section": "SPIROMETRY",
                "page": 38,
                "chunk_id": "gold-2026:abc",
            }
        ],
    )
    valid, problems = CitationValidator().validate(answer, evidence())
    assert valid
    assert problems == []


def test_citation_validator_rejects_fabricated_chunk_id():
    answer = StructuredAnswer(
        "COPD diagnosis requires post-bronchodilator spirometry.",
        ["COPD diagnosis requires post-bronchodilator spirometry."],
        [
            {
                "document": "GOLD 2026 Global Strategy Report",
                "source_filename": "GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf",
                "section": "SPIROMETRY",
                "page": 38,
                "chunk_id": "gold-2026:fake",
            }
        ],
    )
    valid, problems = CitationValidator().validate(answer, evidence())
    assert not valid
    assert "gold-2026:fake" in problems[0]
