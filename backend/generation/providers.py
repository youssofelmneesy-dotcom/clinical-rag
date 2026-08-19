from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    model_provider: str = "offline"
    query_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    generation_model: str = "extractive-offline"
    verifier_model: str = "deterministic-lexical"
    reranker_model: str = "deterministic-hybrid-reranker"
    openrouter_api_key: str | None = None
    ollama_base_url: str | None = None

    @classmethod
    def from_env(cls) -> "ModelConfig":
        return cls(
            model_provider=os.getenv("MODEL_PROVIDER", "offline"),
            query_model=os.getenv("QUERY_MODEL", os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")),
            generation_model=os.getenv("GENERATION_MODEL", os.getenv("OPENAI_MODEL", "extractive-offline")),
            verifier_model=os.getenv("VERIFIER_MODEL", "deterministic-lexical"),
            reranker_model=os.getenv("RERANKER_MODEL", "deterministic-hybrid-reranker"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
        )
