#!/usr/bin/env python3
"""
Retrieval Precision Optimization Experiments.

Systematically test different hybrid retrieval configurations
to find the best Pareto-optimal settings.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import EVALUATION_DATASET_PATH, EVALUATION_DIR
from backend.evaluation import load_evaluation_dataset, evaluate_retrieval
from backend.retrieval.hybrid import HybridRetriever, HybridRetrievalConfig


@dataclass(frozen=True)
class ExperimentResult:
    name: str
    dense_weight: float
    lexical_weight: float
    candidate_k: int
    precision_at_3: float
    precision_at_5: float
    precision_at_10: float
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    hit_rate_at_5: float
    latency_ms: float
    query_count: int


def evaluate_configuration(
    config: HybridRetrievalConfig,
    records: list,
    name: str,
    k_values: list[int] = [3, 5, 10],
) -> dict[str, Any]:
    """Evaluate a retrieval configuration using the official evaluation logic."""
    retriever = HybridRetriever(config=config)

    results_by_k = {}
    total_latency = 0.0
    query_count = 0

    for k in k_values:
        t0 = time.perf_counter()
        report = evaluate_retrieval(records, retriever, k=k)
        t1 = time.perf_counter()
        total_latency += (t1 - t0) * 1000
        query_count += report["record_count"]

        results_by_k[k] = {
            "precision": report["precision_at_k"],
            "recall": report["recall_at_k"],
            "hit_rate": report["hit_rate_at_k"],
        }

    avg_latency_ms = total_latency / max(1, len(k_values))

    return {
        "name": name,
        "dense_weight": config.dense_weight,
        "lexical_weight": config.lexical_weight,
        "candidate_k": config.candidate_k,
        "precision_at_3": results_by_k.get(3, {}).get("precision", 0.0),
        "precision_at_5": results_by_k.get(5, {}).get("precision", 0.0),
        "precision_at_10": results_by_k.get(10, {}).get("precision", 0.0),
        "recall_at_3": results_by_k.get(3, {}).get("recall", 0.0),
        "recall_at_5": results_by_k.get(5, {}).get("recall", 0.0),
        "recall_at_10": results_by_k.get(10, {}).get("recall", 0.0),
        "hit_rate_at_5": results_by_k.get(5, {}).get("hit_rate", 0.0),
        "avg_latency_ms": avg_latency_ms,
        "query_count": len(records),
    }


def main() -> None:
    records = load_evaluation_dataset(EVALUATION_DATASET_PATH)
    experiments = []

    # Test 1: Dense weights sweep (candidate_k=20)
    print("=" * 80)
    print("EXPERIMENT 1: Dense weight sweep (candidate_k=20, final_k=5)")
    print("=" * 80)
    for dense_weight in [0.30, 0.35, 0.40]:
        lexical_weight = 1.0 - dense_weight
        config = HybridRetrievalConfig(
            dense_weight=dense_weight,
            lexical_weight=lexical_weight,
            candidate_k=20,
        )
        result = evaluate_configuration(config, records, f"dense={dense_weight}", k_values=[3, 5, 10])
        experiments.append(result)
        print(
            f"Dense={dense_weight:.2f} Lexical={lexical_weight:.2f}: "
            f"P@5={result['precision_at_5']:.3f} R@5={result['recall_at_5']:.3f} "
            f"Hit@5={result['hit_rate_at_5']:.3f} Latency={result['avg_latency_ms']:.1f}ms"
        )

    # Test 2: Candidate K sweep (dense=0.35)
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: Candidate K sweep (dense=0.35, final_k=5)")
    print("=" * 80)
    for candidate_k in [15, 20, 25, 30]:
        config = HybridRetrievalConfig(
            dense_weight=0.35,
            lexical_weight=0.65,
            candidate_k=candidate_k,
        )
        result = evaluate_configuration(config, records, f"candidate_k={candidate_k}", k_values=[3, 5, 10])
        experiments.append(result)
        print(
            f"Candidate K={candidate_k}: "
            f"P@5={result['precision_at_5']:.3f} R@5={result['recall_at_5']:.3f} "
            f"Hit@5={result['hit_rate_at_5']:.3f} Latency={result['avg_latency_ms']:.1f}ms"
        )

    # Test 3: Combined best combinations
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Combined best weight + candidate_k combinations")
    print("=" * 80)
    for dense_weight in [0.30, 0.35, 0.40]:
        for candidate_k in [15, 20, 25]:
            lexical_weight = 1.0 - dense_weight
            config = HybridRetrievalConfig(
                dense_weight=dense_weight,
                lexical_weight=lexical_weight,
                candidate_k=candidate_k,
            )
            result = evaluate_configuration(config, records, f"d={dense_weight}_c={candidate_k}", k_values=[3, 5, 10])
            experiments.append(result)
            print(
                f"Dense={dense_weight:.2f} Candidate K={candidate_k}: "
                f"P@5={result['precision_at_5']:.3f} R@5={result['recall_at_5']:.3f} "
                f"Hit@5={result['hit_rate_at_5']:.3f} Latency={result['avg_latency_ms']:.1f}ms"
            )

    # Save results
    output_path = EVALUATION_DIR / "experiments" / "retrieval_precision_experiments.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(experiments, handle, indent=2)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - Best Pareto configurations (by precision, then by recall)")
    print("=" * 80)
    sorted_by_precision = sorted(experiments, key=lambda e: (-e["precision_at_5"], -e["recall_at_5"]))
    for i, exp in enumerate(sorted_by_precision[:10]):
        print(
            f"{i+1}. {exp['name']}: P@5={exp['precision_at_5']:.3f} R@5={exp['recall_at_5']:.3f} "
            f"Hit@5={exp['hit_rate_at_5']:.3f} Latency={exp['avg_latency_ms']:.1f}ms"
        )

    print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    main()
