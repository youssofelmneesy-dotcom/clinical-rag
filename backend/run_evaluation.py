from __future__ import annotations

from backend.config import EVALUATION_DATASET_PATH
from backend.evaluation import evaluate_retrieval, load_evaluation_dataset, write_evaluation_report
from backend.retrieval.retriever import Retriever


def main() -> None:
    records = load_evaluation_dataset(EVALUATION_DATASET_PATH)
    report = evaluate_retrieval(records, Retriever(), k=5)
    write_evaluation_report(report)
    selected = report["threshold_analysis"]["selected"]
    print(f"Evaluated {report['record_count']} questions")
    print(f"Precision@5: {report['precision_at_k']:.3f}")
    print(f"Recall@5: {report['recall_at_k']:.3f}")
    print(f"Hit Rate@5: {report['hit_rate_at_k']:.3f}")
    print(f"Selected threshold: {selected['selected_threshold']:.2f}")


if __name__ == "__main__":
    main()
