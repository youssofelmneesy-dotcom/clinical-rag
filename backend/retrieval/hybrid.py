from __future__ import annotations

import re
from dataclasses import dataclass

from backend.config import RetrievalConfig
from backend.models import EvidenceResult
from backend.retrieval.lexical import BM25Index, lexical_to_evidence
from backend.retrieval.retriever import Retriever, _expand_query


@dataclass(frozen=True)
class HybridRetrievalConfig:
    dense_weight: float = 0.35
    lexical_weight: float = 0.65
    candidate_k: int = 20


class HybridRetriever:
    def __init__(
        self,
        dense_retriever: Retriever | None = None,
        bm25: BM25Index | None = None,
        config: HybridRetrievalConfig | None = None,
    ) -> None:
        self.dense_retriever = dense_retriever or Retriever()
        self.bm25 = bm25 or BM25Index()
        self.config = config or HybridRetrievalConfig()

    def retrieve(self, question: str, k: int | None = None) -> list[EvidenceResult]:
        final_k = k or RetrievalConfig().default_k
        candidate_k = max(self.config.candidate_k, final_k)
        expanded_query = _expand_query(question)
        dense = self.dense_retriever.retrieve(question, k=candidate_k)
        lexical = [lexical_to_evidence(item) for item in self.bm25.search(expanded_query, k=candidate_k)]
        fused = _fuse(question, dense, lexical, self.config)
        return fused[:final_k]


def _fuse(
    question: str,
    dense: list[EvidenceResult],
    lexical: list[EvidenceResult],
    config: HybridRetrievalConfig,
) -> list[EvidenceResult]:
    by_id: dict[str, EvidenceResult] = {}
    scores: dict[str, float] = {}
    
    # Fuse rankings with weighted reciprocal rank fusion
    for rank, item in enumerate(dense, start=1):
        by_id[item.chunk_id] = item
        # RRF formula with dense weight
        scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + config.dense_weight * (1.0 / (1.0 + rank))
    
    for rank, item in enumerate(lexical, start=1):
        by_id.setdefault(item.chunk_id, item)
        # RRF formula with lexical weight
        scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + config.lexical_weight * (1.0 / (1.0 + rank))
    
    query_terms = _content_terms(question)
    reranked = []
    
    for chunk_id, item in by_id.items():
        overlap = _overlap_bonus(query_terms, item)
        section_bonus = _section_bonus(query_terms, item.section)
        document_bonus = _document_bonus(question, item)
        noise_penalty = _noise_penalty(item)
        diversity_penalty = _diversity_penalty_score(item, list(by_id.values()))
        
        fused_score = scores[chunk_id] + overlap + section_bonus + document_bonus - noise_penalty - diversity_penalty
        reranked.append((fused_score, item))
    
    reranked.sort(key=lambda pair: (pair[0], pair[1].similarity), reverse=True)
    
    # Apply MMR-style diversity selection to top results
    final_results = _apply_mmr_diversity(reranked)
    
    return [_with_hybrid_score(item, score) for score, item in final_results]


def _with_hybrid_score(item: EvidenceResult, score: float) -> EvidenceResult:
    metadata = dict(item.metadata)
    metadata["hybrid_score"] = score
    return EvidenceResult(
        chunk_id=item.chunk_id,
        text=item.text,
        distance=item.distance,
        similarity=item.similarity,
        document=item.document,
        page=item.page,
        section=item.section,
        metadata=metadata,
    )


def _content_terms(text: str) -> set[str]:
    stop = {
        "what",
        "when",
        "how",
        "does",
        "about",
        "recommended",
        "recommend",
        "copd",
        "patients",
        "people",
    }
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in stop and len(token) > 2}


def _overlap_bonus(query_terms: set[str], item: EvidenceResult) -> float:
    if not query_terms:
        return 0.0
    evidence_terms = set(re.findall(r"[a-z0-9]+", f"{item.section} {item.text}".lower()))
    return 0.08 * (len(query_terms.intersection(evidence_terms)) / len(query_terms))


def _section_bonus(query_terms: set[str], section: str) -> float:
    section_terms = set(re.findall(r"[a-z0-9]+", section.lower()))
    if not query_terms:
        return 0.0
    return 0.05 * (len(query_terms.intersection(section_terms)) / len(query_terms))


def _document_bonus(question: str, item: EvidenceResult) -> float:
    normalized = question.lower()
    document_id = str(item.metadata.get("document_id", ""))
    if "nice" in normalized and document_id == "nice-ng115":
        return 0.12
    if "gold" in normalized and document_id == "gold-2026":
        return 0.12
    return 0.0


def _noise_penalty(item: EvidenceResult) -> float:
    text = item.text.lower()
    section = item.section.lower()
    penalty = 0.0
    if section in {"background", "methodology", "key points:"}:
        penalty += 0.03
    if "all rights reserved" in text or "medical research council dyspnoea scale" in text:
        penalty += 0.03
    if "hospital/ed where date length reason" in text:
        penalty += 0.05
    return penalty


def _diversity_penalty_score(item: EvidenceResult, all_items: list[EvidenceResult]) -> float:
    """Penalize chunks that are very similar to their neighbors."""
    text_lower = item.text.lower()
    text_tokens = set(re.findall(r"[a-z0-9]+", text_lower))
    if not text_tokens:
        return 0.0
    
    max_overlap = 0.0
    for other in all_items:
        if other.chunk_id == item.chunk_id:
            continue
        other_lower = other.text.lower()
        other_tokens = set(re.findall(r"[a-z0-9]+", other_lower))
        if not other_tokens:
            continue
        
        overlap = len(text_tokens & other_tokens) / min(len(text_tokens), len(other_tokens))
        max_overlap = max(max_overlap, overlap)
    
    # Penalize high overlap (potential redundancy)
    if max_overlap > 0.75:
        return 0.10
    elif max_overlap > 0.60:
        return 0.05
    return 0.0


def _apply_mmr_diversity(scored_items: list[tuple[float, EvidenceResult]], lambda_param: float = 0.8) -> list[tuple[float, EvidenceResult]]:
    """
    Apply Maximal Marginal Relevance (MMR) style diversity selection.
    
    Prevents redundant highly-similar chunks from dominating the result set.
    lambda_param: balance between relevance (1.0) and diversity (0.0)
    """
    if len(scored_items) <= 5:
        return scored_items
    
    selected = []
    candidates = list(scored_items)
    
    while candidates and len(selected) < len(scored_items):
        if not selected:
            # Pick the highest-scoring item first
            best_idx = 0
            selected.append(candidates.pop(0))
        else:
            # Pick item that balances relevance and diversity
            best_idx = 0
            best_mmr = float('-inf')
            
            for i, (score, item) in enumerate(candidates):
                # Relevance component
                relevance = score
                
                # Diversity component: maximum similarity to already-selected items
                max_similarity = 0.0
                for _, selected_item in selected:
                    similarity = _text_similarity(item.text, selected_item.text)
                    max_similarity = max(max_similarity, similarity)
                
                # MMR score: balance relevance and diversity
                mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_similarity
                
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = i
            
            selected.append(candidates.pop(best_idx))
    
    return selected


def _text_similarity(text1: str, text2: str) -> float:
    """
    Compute Jaccard similarity between two text snippets.
    Used for MMR diversity calculation.
    """
    tokens1 = set(re.findall(r"[a-z0-9]+", text1.lower()))
    tokens2 = set(re.findall(r"[a-z0-9]+", text2.lower()))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0
