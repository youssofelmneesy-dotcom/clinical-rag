#!/usr/bin/env python3
"""
Efficient retrieval optimization - test configs with preloaded models.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from backend.config import EVALUATION_DATASET_PATH, EVALUATION_DIR
from backend.evaluation import evaluate_retrieval, load_evaluation_dataset
from backend.retrieval.hybrid import HybridRetriever, HybridRetrievalConfig
from backend.retrieval.retriever import Retriever
from backend.retrieval.lexical import BM25Index


def main() -> None:
    records = load_evaluation_dataset(EVALUATION_DATASET_PATH)

    # Pre-load all shared resources ONCE
    print("Loading models and indexes...")
    t0 = time.perf_counter()
    dense_retriever = Retriever()
    bm25 = BM25Index()
    t1 = time.perf_counter()
    print(f"Models loaded in {(t1 - t0) * 1000:.0f}ms")

    experiments = []

    # Test configurations with pre-loaded models
    configs = [
        ("baseline", HybridRetrievalConfig(dense_weight=0.35, lexical_weight=0.65, candidate_k=20)),
        ("dense-boost", HybridRetrievalConfig(dense_weight=0.40, lexical_weight=0.60, candidate_k=20)),
        ("lex-boost", HybridRetrievalConfig(dense_weight=0.30, lexical_weight=0.70, candidate_k=20)),
        ("candidate-30", HybridRetrievalConfig(dense_weight=0.35, lexical_weight=0.65, candidate_k=30)),
        ("candidate-15", HybridRetrievalConfig(dense_weight=0.35, lexical_weight=0.65, candidate_k=15)),
        ("dense-45", HybridRetrievalConfig(dense_weight=0.45, lexical_weight=0.55, candidate_k=20)),
        ("balanced-25", HybridRetrievalConfig(dense_weight=0.50, lexical_weight=0.50, candidate_k=25)),
    ]

    print("=" * 80)
    print("RETRIEVAL CONFIGURATION EXPERIMENTS")
    print("=" * 80)

    for name, config in configs:
        t0 = time.perf_counter()
        retriever = HybridRetriever(dense_retriever=dense_retriever, bm25=bm25, config=config)
        report = evaluate_retrieval(records, retriever, k=5)
        t1 = time.perf_counter()

        result = {
            "name": name,
            "dense_weight": config.dense_weight,
            "lexical_weight": config.lexical_weight,
            "candidate_k": config.candidate_k,
            "precision_at_5": report["precision_at_k"],
            "recall_at_5": report["recall_at_k"],
            "hit_rate_at_5": report["hit_rate_at_k"],
            "evaluation_time_ms": (t1 - t0) * 1000,
        }
        experiments.append(result)

        print(
            f"{name:20s}: P@5={result['precision_at_5']:.3f} R@5={result['recall_at_5']:.3f} Hit@5={result['hit_rate_at_5']:.3f} Time={result['evaluation_time_ms']:.0f}ms"
        )

    # Save results
    output_dir = EVALUATION_DIR / "experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "optimization_results.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(experiments, handle, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Summary
    print("\n" + "=" * 80)
    print("BEST CONFIGURATION (by Precision@5)")
    print("=" * 80)
    best = max(experiments, key=lambda e: e["precision_at_5"])
    print(f"Name: {best['name']}")
    print(f"Dense weight: {best['dense_weight']:.2f}")
    print(f"Lexical weight: {best['lexical_weight']:.2f}")
    print(f"Candidate K: {best['candidate_k']}")
    print(f"Precision@5: {best['precision_at_5']:.3f}")
    print(f"Recall@5: {best['recall_at_5']:.3f}")
    print(f"Hit@5: {best['hit_rate_at_5']:.3f}")

    print("\n" + "=" * 80)
    print("ALL RESULTS RANKED BY PRECISION@5")
    print("=" * 80)
    for rank, exp in enumerate(sorted(experiments, key=lambda e: e["precision_at_5"], reverse=True), 1):
        print(f"{rank}. {exp['name']:20s}: P@5={exp['precision_at_5']:.3f} R@5={exp['recall_at_5']:.3f} Hit@5={exp['hit_rate_at_5']:.3f}")


if __name__ == "__main__":
    main()
