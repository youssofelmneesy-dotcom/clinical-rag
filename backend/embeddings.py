from __future__ import annotations

import hashlib
import math
import os
from typing import Protocol

from backend.config import EmbeddingConfig


class EmbeddingService(Protocol):
    @property
    def dimension(self) -> int:
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class SentenceTransformerEmbeddingService:
    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self.config = config or EmbeddingConfig(model_name=os.getenv("EMBEDDING_MODEL", os.getenv("QUERY_MODEL", EmbeddingConfig().model_name)))
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for local clinical text embeddings. "
                "Install requirements.txt before running ingestion or retrieval."
            ) from exc
        self.model = SentenceTransformer(self.config.model_name)
        dimension_getter = getattr(self.model, "get_embedding_dimension", self.model.get_sentence_embedding_dimension)
        self._dimension = int(dimension_getter())

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class DeterministicHashEmbeddingService:
    """Small deterministic embedding service for tests and offline smoke checks."""

    def __init__(self, dimension: int = 64) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def default_embedding_service() -> EmbeddingService:
    return SentenceTransformerEmbeddingService()
