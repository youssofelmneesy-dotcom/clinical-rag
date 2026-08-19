from pathlib import Path

from backend.config import SourceDocument
from backend.ingestion.knowledge_base import build_chunks, load_chunks


def test_build_chunks_uses_explicit_sources(monkeypatch, tmp_path: Path):
    sources = (
        SourceDocument("gold-2026", "GOLD", "gold.pdf", "clinical_guideline"),
        SourceDocument("nice-ng115", "NICE", "nice.pdf", "clinical_guideline"),
    )

    def fake_extract(path: str):
        return [{"page": 1, "text": "1.1 Diagnosing COPD\nConfirm COPD with spirometry and clinical assessment."}]

    monkeypatch.setattr("backend.ingestion.knowledge_base.extract_text_from_pdf", fake_extract)
    output = tmp_path / "chunks.jsonl"
    chunks = build_chunks(sources=sources, output_path=output)
    loaded = load_chunks(output)
    assert {chunk.document_id for chunk in chunks} == {"gold-2026", "nice-ng115"}
    assert len(loaded) == len(chunks)
    assert all(chunk.source_filename in {"gold.pdf", "nice.pdf"} for chunk in loaded)
