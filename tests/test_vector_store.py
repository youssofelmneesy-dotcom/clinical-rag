import importlib.util

import pytest

from backend.embeddings import DeterministicHashEmbeddingService
from backend.models import Chunk
from backend.retrieval.vector_store import ChromaVectorStore


pytestmark = pytest.mark.skipif(importlib.util.find_spec("chromadb") is None, reason="chromadb is not installed")


def test_chroma_upsert_is_idempotent(tmp_path):
    chunk = Chunk(
        chunk_id="gold-2026:test",
        document_id="gold-2026",
        document_name="GOLD",
        source_filename="gold.pdf",
        page=1,
        section="Diagnosis",
        text="COPD diagnosis is confirmed by spirometry.",
    )
    store = ChromaVectorStore(tmp_path, embedding_service=DeterministicHashEmbeddingService())
    first_count = store.upsert_chunks([chunk])
    second_count = store.upsert_chunks([chunk])
    results = store.search("How is COPD diagnosed?", k=1)
    assert first_count == second_count == 1
    assert results[0].chunk_id == chunk.chunk_id


def test_chroma_sync_removes_stale_deterministic_ids(tmp_path):
    first = Chunk(
        chunk_id="gold-2026:old",
        document_id="gold-2026",
        document_name="GOLD",
        source_filename="gold.pdf",
        page=1,
        section="Diagnosis",
        text="Old COPD text.",
    )
    second = Chunk(
        chunk_id="gold-2026:new",
        document_id="gold-2026",
        document_name="GOLD",
        source_filename="gold.pdf",
        page=1,
        section="Diagnosis",
        text="New COPD spirometry text.",
    )
    store = ChromaVectorStore(tmp_path, embedding_service=DeterministicHashEmbeddingService())
    store.upsert_chunks([first])
    count = store.sync_chunks([second])
    assert count == 1
    assert store.search("spirometry", k=1)[0].chunk_id == "gold-2026:new"
