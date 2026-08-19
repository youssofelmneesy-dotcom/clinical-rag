from backend.evaluation import EvaluationRecord, evaluate_retrieval
from backend.models import EvidenceResult


class FakeRetriever:
    def retrieve(self, question: str, k: int = 5):
        return [
            EvidenceResult(
                chunk_id="gold-2026:1",
                text="Confirm COPD using post-bronchodilator FEV1/FVC spirometry.",
                distance=0.1,
                similarity=0.9,
                document="GOLD",
                page=1,
                section="Diagnosis",
                metadata={"document_id": "gold-2026"},
            )
        ]


def test_retrieval_evaluation_uses_real_retriever_results():
    records = [
        EvaluationRecord(
            question="How is COPD confirmed?",
            category="in_scope",
            answerable=True,
            expected_document="gold-2026",
            expected_terms=["spirometry"],
        )
    ]
    report = evaluate_retrieval(records, FakeRetriever(), k=1)
    assert report["precision_at_k"] == 1.0
    assert report["recall_at_k"] == 1.0
    assert report["threshold_analysis"]["selected"]["selected_threshold"] > 0
