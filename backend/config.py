from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
GUIDELINES_DIR = DATA_DIR / "guidelines"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"
CHROMA_PATH = DATA_DIR / "chroma"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
EVALUATION_DATASET_PATH = EVALUATION_DIR / "retrieval_eval.jsonl"
EVALUATION_REPORT_PATH = EVALUATION_DIR / "retrieval_report.json"
CONFIDENCE_CONFIG_PATH = EVALUATION_DIR / "confidence_threshold.json"


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    document_name: str
    filename: str
    source_type: str
    publisher: str | None = None
    version: str | None = None
    source_url: str | None = None
    legal_notes: str | None = None
    publication_date: str | None = None
    update_date: str | None = None
    jurisdiction: str | None = None

    @property
    def path(self) -> Path:
        return GUIDELINES_DIR / self.filename


VALID_SOURCE_DOCUMENTS: tuple[SourceDocument, ...] = (
    SourceDocument(
        document_id="gold-2026",
        document_name="GOLD 2026 Global Strategy Report",
        filename="GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf",
        source_type="clinical_guideline",
        publisher="Global Initiative for Chronic Obstructive Lung Disease",
        version="2026 v1.3",
        source_url="https://goldcopd.org/2026-gold-report/",
        legal_notes="Included as an official COPD strategy report for local evidence-grounded retrieval.",
        publication_date="2025-12-08",
        jurisdiction="global",
    ),
    SourceDocument(
        document_id="nice-ng115",
        document_name="NICE NG115: Chronic obstructive pulmonary disease in over 16s: diagnosis and management",
        filename="chronic-obstructive-pulmonary-disease-in-over-16s-diagnosis-and-management-pdf-66141600098245.pdf",
        source_type="clinical_guideline",
        publisher="National Institute for Health and Care Excellence",
        version="NG115",
        source_url="https://www.nice.org.uk/guidance/ng115",
        legal_notes="Included as an official NICE COPD guideline for local evidence-grounded retrieval.",
        jurisdiction="United Kingdom",
    ),
)


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 1400
    chunk_overlap: int = 180
    min_chunk_size: int = 180


@dataclass(frozen=True)
class RetrievalConfig:
    collection_name: str = "copd_guidelines"
    default_k: int = 5
    chroma_distance_metric: str = "cosine"


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
