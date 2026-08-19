from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from backend.config import CHUNKS_PATH
from backend.ingestion.knowledge_base import load_chunks
from backend.models import Chunk, EvidenceResult


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "with",
}


@dataclass(frozen=True)
class LexicalResult:
    chunk: Chunk
    score: float


class BM25Index:
    def __init__(self, chunks: list[Chunk] | None = None, k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks if chunks is not None else load_chunks(CHUNKS_PATH)
        self.k1 = k1
        self.b = b
        self.tokenized = [_tokens(chunk.text, chunk.section) for chunk in self.chunks]
        self.lengths = [len(tokens) for tokens in self.tokenized]
        self.avgdl = sum(self.lengths) / max(1, len(self.lengths))
        self.doc_freqs = _document_frequencies(self.tokenized)
        self.corpus_size = len(self.chunks)

    def search(self, query: str, k: int = 20) -> list[LexicalResult]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []
        scored = []
        for index, document_tokens in enumerate(self.tokenized):
            score = self._score(query_tokens, document_tokens, self.lengths[index])
            if score > 0:
                scored.append(LexicalResult(self.chunks[index], score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:k]

    def _score(self, query_tokens: list[str], document_tokens: list[str], doc_length: int) -> float:
        frequencies = Counter(document_tokens)
        score = 0.0
        for token in query_tokens:
            if token not in frequencies:
                continue
            df = self.doc_freqs.get(token, 0)
            idf = math.log(1 + (self.corpus_size - df + 0.5) / (df + 0.5))
            term_frequency = frequencies[token]
            denominator = term_frequency + self.k1 * (1 - self.b + self.b * doc_length / max(1.0, self.avgdl))
            score += idf * (term_frequency * (self.k1 + 1)) / denominator
        return score


def lexical_to_evidence(result: LexicalResult) -> EvidenceResult:
    chunk = result.chunk
    metadata = chunk.to_json()
    metadata.pop("text", None)
    return EvidenceResult(
        chunk_id=chunk.chunk_id,
        text=chunk.text,
        distance=1.0 / (1.0 + result.score),
        similarity=result.score / (1.0 + result.score),
        document=chunk.document_name,
        page=chunk.page,
        section=chunk.section,
        metadata=metadata,
    )


def _document_frequencies(tokenized_documents: list[list[str]]) -> dict[str, int]:
    frequencies: Counter[str] = Counter()
    for tokens in tokenized_documents:
        frequencies.update(set(tokens))
    return dict(frequencies)


def _tokens(*texts: str) -> list[str]:
    tokens: list[str] = []
    for text in texts:
        tokens.extend(
            token
            for token in TOKEN_PATTERN.findall(text.lower())
            if token not in STOPWORDS and len(token) > 2
        )
    return tokens
