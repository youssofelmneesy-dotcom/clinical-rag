from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.config import CHROMA_PATH, RetrievalConfig
from backend.embeddings import EmbeddingService, default_embedding_service
from backend.models import Chunk, EvidenceResult


class ChromaVectorStore:
    def __init__(
        self,
        persist_path: Path = CHROMA_PATH,
        config: RetrievalConfig | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.config = config or RetrievalConfig()
        self.embedding_service = embedding_service or default_embedding_service()
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is required for persistent local retrieval. Install requirements.txt.") from exc
        persist_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": self.config.chroma_distance_metric},
        )

    def upsert_chunks(self, chunks: list[Chunk], batch_size: int = 64) -> int:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = self.embedding_service.embed_texts([chunk.text for chunk in batch])
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                embeddings=embeddings,
                metadatas=[_metadata(chunk) for chunk in batch],
            )
        return int(self.collection.count())

    def sync_chunks(self, chunks: list[Chunk], batch_size: int = 64) -> int:
        desired_ids = {chunk.chunk_id for chunk in chunks}
        existing = self.collection.get()
        stale_ids = [chunk_id for chunk_id in existing.get("ids", []) if chunk_id not in desired_ids]
        if stale_ids:
            self.collection.delete(ids=stale_ids)
        return self.upsert_chunks(chunks, batch_size=batch_size)

    def search(self, query: str, k: int | None = None) -> list[EvidenceResult]:
        query_embedding = self.embedding_service.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k or self.config.default_k,
            include=["documents", "distances", "metadatas"],
        )
        return _to_evidence_results(result)

    def count(self) -> int:
        return int(self.collection.count())


def _metadata(chunk: Chunk) -> dict[str, Any]:
    data = chunk.to_json()
    data.pop("text", None)
    return data


def _to_evidence_results(result: dict[str, Any]) -> list[EvidenceResult]:
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    evidence: list[EvidenceResult] = []
    for chunk_id, text, distance, metadata in zip(ids, documents, distances, metadatas):
        similarity = 1.0 - float(distance)
        evidence.append(
            EvidenceResult(
                chunk_id=chunk_id,
                text=text,
                distance=float(distance),
                similarity=similarity,
                document=str(metadata.get("document_name", "")),
                page=int(metadata.get("page", 0)),
                section=str(metadata.get("section", "Unknown")),
                metadata=dict(metadata),
            )
        )
    return evidence
