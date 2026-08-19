from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.config import EVALUATION_DATASET_PATH, EVALUATION_DIR
from backend.evaluation import evaluate_retrieval, load_evaluation_dataset
from backend.models import EvidenceResult
from backend.retrieval.hybrid import HybridRetriever
from backend.retrieval.lexical import BM25Index, lexical_to_evidence
from backend.retrieval.retriever import Retriever


EXPERIMENT_REPORT_PATH = EVALUATION_DIR / "retrieval_experiments.json"


class BM25Retriever:
    def __init__(self) -> None:
        self.index = BM25Index()

    def retrieve(self, question: str, k: int = 5) -> list[EvidenceResult]:
        return [lexical_to_evidence(item) for item in self.index.search(question, k=k)]


def run_experiments() -> dict[str, Any]:
    records = load_evaluation_dataset(EVALUATION_DATASET_PATH)
    experiments = {
        "dense": Retriever(),
        "bm25": BM25Retriever(),
        "hybrid": HybridRetriever(),
    }
    results: dict[str, Any] = {}
    for name, retriever in experiments.items():
        results[name] = {}
        for k in (3, 5, 10):
            report = evaluate_retrieval(records, retriever, k=k)
            results[name][f"k_{k}"] = {
                "precision_at_k": report["precision_at_k"],
                "recall_at_k": report["recall_at_k"],
                "hit_rate_at_k": report["hit_rate_at_k"],
                "selected_threshold": report["threshold_analysis"]["selected"],
            }
    EXPERIMENT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXPERIMENT_REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    return results


def main() -> None:
    results = run_experiments()
    for name, by_k in results.items():
        print(name)
        for k, metrics in by_k.items():
            print(
                f"  {k}: precision={metrics['precision_at_k']:.3f} "
                f"recall={metrics['recall_at_k']:.3f} hit={metrics['hit_rate_at_k']:.3f} "
                f"threshold={metrics['selected_threshold']['selected_threshold']:.2f}"
            )


if __name__ == "__main__":
    main()
