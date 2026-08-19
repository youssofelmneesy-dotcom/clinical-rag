from backend.models import Chunk, EvidenceResult
from backend.retrieval.hybrid import HybridRetriever
from backend.retrieval.lexical import BM25Index


def test_bm25_prefers_exact_clinical_terms():
    chunks = [
        Chunk("c1", "gold-2026", "GOLD", "gold.pdf", 1, "Diagnosis", "COPD diagnosis uses spirometry."),
        Chunk("c2", "gold-2026", "GOLD", "gold.pdf", 2, "Background", "General report background text."),
    ]
    index = BM25Index(chunks)
    results = index.search("COPD spirometry", k=2)
    assert results[0].chunk.chunk_id == "c1"


class FakeDenseRetriever:
    def retrieve(self, question: str, k: int = 5):
        return [
            EvidenceResult("c2", "General report background text.", 0.2, 0.8, "GOLD", 2, "Background", {"document_id": "gold-2026"}),
            EvidenceResult("c1", "COPD diagnosis uses spirometry.", 0.3, 0.7, "GOLD", 1, "Diagnosis", {"document_id": "gold-2026"}),
        ]


def test_hybrid_reranks_lexically_relevant_candidate():
    chunks = [
        Chunk("c1", "gold-2026", "GOLD", "gold.pdf", 1, "Diagnosis", "COPD diagnosis uses spirometry."),
        Chunk("c2", "gold-2026", "GOLD", "gold.pdf", 2, "Background", "General report background text."),
    ]
    retriever = HybridRetriever(dense_retriever=FakeDenseRetriever(), bm25=BM25Index(chunks))
    results = retriever.retrieve("How is COPD diagnosis confirmed with spirometry?", k=1)
    assert results[0].chunk_id == "c1"
