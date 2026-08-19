from __future__ import annotations

from backend.models import Chunk
from backend.retrieval.vector_store import ChromaVectorStore


def index_chunks(chunks: list[Chunk]) -> int:
    store = ChromaVectorStore()
    return store.sync_chunks(chunks)
