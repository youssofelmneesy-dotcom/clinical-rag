from backend.generation.generator import ExtractiveAnswerGenerator, _grounding_prompt, _parse_structured_text
from backend.models import EvidenceResult, StructuredAnswer
from backend.pipeline import ClinicalRagPipeline
from backend.safety.claim_verifier import ClaimVerifier
from backend.safety.confidence import ConfidenceGate
from backend.safety.scope import ScopeDetector


EVIDENCE = [
    EvidenceResult(
        chunk_id="nice-ng115:1",
        text="COPD diagnosis should include spirometry. Pulmonary rehabilitation is recommended for suitable people with COPD.",
        distance=0.08,
        similarity=0.92,
        document="NICE NG115",
        page=10,
        section="Diagnosis",
        metadata={
            "document_id": "nice-ng115",
            "document_name": "NICE NG115",
            "source_filename": "nice.pdf",
            "page": 10,
            "section": "Diagnosis",
        },
    )
]


class FakeRetriever:
    def __init__(self, evidence=None):
        self.evidence = evidence if evidence is not None else EVIDENCE

    def retrieve(self, question: str, k: int = 5):
        return self.evidence


def test_scope_detector_rejects_out_of_domain_question():
    decision = ScopeDetector().decide("What is the recommended treatment for diabetes?", EVIDENCE)
    assert not decision.in_scope


def test_confidence_gate_accepts_and_rejects_by_threshold():
    gate = ConfidenceGate(threshold=0.5)
    assert gate.decide(EVIDENCE).sufficient
    assert not gate.decide([]).sufficient
    assert not gate.decide(EVIDENCE, "What is the best COPD inhaler for a patient with missing spirometry?").sufficient


def test_extractive_generation_returns_structured_sources():
    answer = ExtractiveAnswerGenerator().generate("What does COPD diagnosis include?", EVIDENCE)
    assert "spirometry" in answer.render().lower()
    assert answer.sources[0]["page"] == 10
    assert answer.sources[0]["source_filename"] == "nice.pdf"
    assert "Chunk: nice-ng115:1" in answer.render()


def test_grounding_prompt_requires_json_and_source_traceability():
    prompt = _grounding_prompt("What does COPD diagnosis include?", EVIDENCE)
    assert "Return valid JSON only" in prompt
    assert "source_filename" in prompt
    assert "chunk_id: nice-ng115:1" in prompt


def test_json_generation_parser_keeps_only_retrieved_sources():
    text = """
    {
      "recommendation": "COPD diagnosis should include spirometry.",
      "evidence": ["COPD diagnosis should include spirometry."],
      "sources": [
        {"document": "NICE NG115", "source_filename": "nice.pdf", "section": "Diagnosis", "page": 10, "chunk_id": "nice-ng115:1"},
        {"document": "Unknown", "source_filename": "bad.pdf", "section": "Other", "page": 1, "chunk_id": "bad"}
      ],
      "conflicting_guidance": [],
      "insufficient_evidence": false
    }
    """
    answer = _parse_structured_text(text, EVIDENCE)
    assert len(answer.sources) == 1
    assert answer.sources[0]["chunk_id"] == "nice-ng115:1"


def test_claim_verifier_rejects_unsupported_added_claim():
    answer = StructuredAnswer(
        recommendation="COPD diagnosis should include spirometry every 5 years.",
        evidence=["COPD diagnosis should include spirometry every 5 years."],
        sources=[{"document": "NICE NG115", "section": "Diagnosis", "page": 10}],
    )
    result = ClaimVerifier().verify(answer, EVIDENCE)
    assert not result.supported
    assert result.unsupported_claims


def test_claim_verifier_accepts_direct_evidence_claim():
    answer = StructuredAnswer(
        recommendation="COPD diagnosis should include spirometry.",
        evidence=["COPD diagnosis should include spirometry."],
        sources=[{"document": "NICE NG115", "source_filename": "nice.pdf", "section": "Diagnosis", "page": 10, "chunk_id": "nice-ng115:1"}],
    )
    result = ClaimVerifier().verify(answer, EVIDENCE)
    assert result.supported


def test_scope_detector_rejects_unlisted_non_copd_medical_topic():
    decision = ScopeDetector().decide("How should migraine be prevented?", EVIDENCE)
    assert not decision.in_scope


def test_scope_detector_rejects_adjacent_cancer_screening_question():
    decision = ScopeDetector().decide("What screening interval is recommended for COPD lung cancer surveillance?", EVIDENCE)
    assert not decision.in_scope


def test_pipeline_refuses_out_of_scope_before_generation():
    pipeline = ClinicalRagPipeline(
        retriever=FakeRetriever(),
        generator=ExtractiveAnswerGenerator(),
        confidence_gate=ConfidenceGate(threshold=0.5),
    )
    response = pipeline.answer("What is the recommended treatment for diabetes?")
    assert "outside the supported COPD clinical scope" in response.final_text


def test_pipeline_refuses_ambiguous_patient_specific_question():
    pipeline = ClinicalRagPipeline(
        retriever=FakeRetriever(),
        generator=ExtractiveAnswerGenerator(),
        confidence_gate=ConfidenceGate(threshold=0.5),
    )
    response = pipeline.answer("What is the best COPD inhaler for this patient without spirometry?")
    assert "sufficient evidence" in response.final_text


def test_pipeline_returns_grounded_structured_answer():
    pipeline = ClinicalRagPipeline(
        retriever=FakeRetriever(),
        generator=ExtractiveAnswerGenerator(),
        confidence_gate=ConfidenceGate(threshold=0.5),
    )
    response = pipeline.answer("What does COPD diagnosis include?")
    assert "Recommendation:" in response.final_text
    assert response.verification.supported
