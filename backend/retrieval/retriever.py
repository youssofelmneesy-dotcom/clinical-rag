from __future__ import annotations

from backend.config import RetrievalConfig
from backend.models import EvidenceResult
from backend.retrieval.vector_store import ChromaVectorStore


class Retriever:
    def __init__(self, store: ChromaVectorStore | None = None, config: RetrievalConfig | None = None) -> None:
        self.config = config or RetrievalConfig()
        self.store = store or ChromaVectorStore(config=self.config)

    def retrieve(self, question: str, k: int | None = None) -> list[EvidenceResult]:
        results = self.store.search(_expand_query(question), (k or self.config.default_k) * 2)
        return _dedupe_results(results)[: k or self.config.default_k]


def _expand_query(question: str) -> str:
    normalized = question.lower()
    additions: list[str] = []
    if "pharmacological" in normalized or "inhal" in normalized:
        additions.append("bronchodilator LABA LAMA ICS maintenance treatment")
    if "diagnos" in normalized or "spirometry" in normalized:
        additions.append("post-bronchodilator FEV1 FVC airflow obstruction")
    if "exacerbation" in normalized:
        additions.append("acute worsening symptoms dyspnea sputum")
    if "oxygen" in normalized:
        additions.append("long-term oxygen therapy hypoxaemia saturation")
    if "rehabilitation" in normalized:
        additions.append("pulmonary rehabilitation exercise education")
    if "smoking" in normalized:
        additions.append("smoking cessation tobacco")
    return f"{question} {' '.join(additions)}".strip()


def _dedupe_results(results: list[EvidenceResult]) -> list[EvidenceResult]:
    seen: set[str] = set()
    deduped: list[EvidenceResult] = []
    for result in results:
        key = " ".join(result.text.lower().split())[:500]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(result)
    return deduped
