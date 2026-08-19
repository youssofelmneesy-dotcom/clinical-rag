#!/usr/bin/env python3
"""Quick baseline verification."""
from backend.config import EVALUATION_DATASET_PATH
from backend.evaluation import load_evaluation_dataset, evaluate_retrieval
from backend.retrieval.hybrid import HybridRetriever

records = load_evaluation_dataset(EVALUATION_DATASET_PATH)
print(f"Loaded {len(records)} evaluation records")
retriever = HybridRetriever()
print("HybridRetriever initialized")
report = evaluate_retrieval(records, retriever, k=5)
print(f'Precision@5: {report["precision_at_k"]:.3f}')
print(f'Recall@5: {report["recall_at_k"]:.3f}')
print(f'Hit Rate@5: {report["hit_rate_at_k"]:.3f}')
