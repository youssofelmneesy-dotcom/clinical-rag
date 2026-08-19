from backend.config import SourceDocument
from backend.ingestion.chunker import chunk_pages, detect_heading


def source(document_id: str = "nice-ng115") -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        document_name="Test Guideline",
        filename="test.pdf",
        source_type="clinical_guideline",
    )


def test_section_detection_uses_document_specific_patterns():
    assert detect_heading("1.1 Diagnosing COPD", "nice-ng115") == "1.1 Diagnosing COPD"
    assert detect_heading("CHAPTER 3: PREVENTION AND MAINTENANCE THERAPY", "gold-2026")
    assert detect_heading("This is a normal clinical sentence.", "gold-2026") is None


def test_chunking_preserves_recommendation_metadata_and_deterministic_ids():
    pages = [
        {
            "page": 1,
            "text": "\n".join(
                [
                    "1.1 Diagnosing COPD",
                    "1.1.1 Suspect COPD in people with symptoms such as breathlessness, cough or sputum.",
                    "1.1.2 Confirm airflow obstruction using post-bronchodilator spirometry.",
                ]
            ),
        }
    ]
    first = chunk_pages(pages, source())
    second = chunk_pages(pages, source())
    assert first[0].section == "1.1 Diagnosing COPD"
    assert first[0].document_id == "nice-ng115"
    assert first[0].page == 1
    assert first[0].chunk_id == second[0].chunk_id
    assert "post-bronchodilator spirometry" in first[0].text
