from __future__ import annotations

from dataclasses import dataclass

from backend.generation.generator import REFUSAL, AnswerGenerator, default_generator
from backend.models import ClaimVerificationResult, ConfidenceDecision, EvidenceResult, ScopeDecision, StructuredAnswer
from backend.retrieval.retriever import Retriever
from backend.safety.claim_verifier import ClaimVerifier
from backend.safety.confidence import ConfidenceGate
from backend.safety.scope import ScopeDetector


@dataclass(frozen=True)
class RagResponse:
    question: str
    scope: ScopeDecision
    confidence: ConfidenceDecision
    evidence: list[EvidenceResult]
    answer: StructuredAnswer
    verification: ClaimVerificationResult
    final_text: str


class ClinicalRagPipeline:
    def __init__(
        self,
        retriever: Retriever | None = None,
        generator: AnswerGenerator | None = None,
        scope_detector: ScopeDetector | None = None,
        confidence_gate: ConfidenceGate | None = None,
        verifier: ClaimVerifier | None = None,
    ) -> None:
        self.retriever = retriever or Retriever()
        self.generator = generator or default_generator()
        self.scope_detector = scope_detector or ScopeDetector()
        self.confidence_gate = confidence_gate or ConfidenceGate()
        self.verifier = verifier or ClaimVerifier()

    def answer(self, question: str, k: int = 5) -> RagResponse:
        evidence = self.retriever.retrieve(question, k=k)
        scope = self.scope_detector.decide(question, evidence)
        confidence = self.confidence_gate.decide(evidence, question)
        if not scope.in_scope:
            answer = StructuredAnswer(
                recommendation="This question is outside the supported COPD clinical scope.",
                evidence=[],
                sources=[],
                insufficient_evidence=True,
            )
            verification = self.verifier.verify(answer, evidence)
            return RagResponse(question, scope, confidence, evidence, answer, verification, answer.render())
        if not confidence.sufficient:
            answer = StructuredAnswer(recommendation=REFUSAL, evidence=[], sources=[], insufficient_evidence=True)
            verification = self.verifier.verify(answer, evidence)
            return RagResponse(question, scope, confidence, evidence, answer, verification, answer.render())
        answer = self.generator.generate(question, evidence)
        verification = self.verifier.verify(answer, evidence)
        final_text = answer.render() if verification.supported else REFUSAL
        return RagResponse(question, scope, confidence, evidence, answer, verification, final_text)
