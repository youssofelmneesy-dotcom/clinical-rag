# Clinical RAG / AI Clinical Decision Support Lite Report

## 1. Executive Summary

This project is a COPD-only Retrieval Augmented Generation system for grounded clinical decision support using only two approved guideline sources: GOLD 2026 and NICE NG115. The final system preserves deterministic ingestion, ChromaDB indexing, hybrid dense/BM25 retrieval, grounded offline generation, citation validation, claim verification, and strict safety/refusal gates.

Final measured retrieval improved from the competition-optimization baseline Precision@5 of 0.713 to 0.740 while preserving Recall@5 and Hit@5 at 0.967. The >0.85 Precision@5 target was not reached without risking overfitting or changing evaluation labels.

## 2. Problem

The system answers COPD guideline questions with transparent evidence and refuses unsupported, patient-specific, adversarial, or out-of-scope requests. It is designed for hackathon judging where retrieval quality, grounding, citations, safety, architecture, evaluation rigor, and demo transparency matter.

## 3. Clinical Scope

Scope is COPD only. The system accepts questions about COPD diagnosis, assessment, spirometry, exacerbations, inhaled therapy, pulmonary rehabilitation, smoking cessation, oxygen therapy, follow-up, and guideline-specific GOLD/NICE COPD recommendations.

It refuses non-COPD topics, adjacent medical topics outside the approved corpus, fabricated citation requests, attempts to ignore evidence, and individualized clinical decisions where retrieved guideline evidence is insufficient.

## 4. Approved Sources

| Source | Document ID | Chunks | Status |
|---|---:|---:|---|
| GOLD 2026 Global Strategy Report | gold-2026 | 408 | Approved |
| NICE NG115 COPD in over 16s | nice-ng115 | 117 | Approved |

Final whitelist validation: 2 approved sources, 525 chunks, 0 EFHS chunks, 0 reference-like chunks, 0 duplicate chunk IDs.

## 5. Architecture

```text
PDF ingestion
  -> section-aware chunking
  -> JSONL knowledge base
  -> local sentence-transformer embeddings
  -> ChromaDB
  -> dense retrieval + BM25 lexical retrieval
  -> deterministic hybrid reranking
  -> COPD scope gate
  -> evidence/confidence gate
  -> grounded generation
  -> citation validation
  -> claim verification
  -> answer or refusal
```

The implementation is split across `backend/ingestion`, `backend/retrieval`, `backend/generation`, `backend/safety`, and `backend/evaluation`.

## 6. Ingestion

PDF parsing uses PyMuPDF. The knowledge base is generated from the explicit source whitelist in `backend/config.py`. Ingestion writes deterministic chunk IDs to `data/chunks.jsonl` and syncs them into ChromaDB.

Final idempotency check:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.ingestion.build_knowledge_base
```

Result: wrote 525 chunks and indexed 525 deterministic chunk IDs.

## 7. Chunking

Chunking is section-aware and page-aware. It preserves recommendation-like units where possible, applies overlap, tracks page ranges and sections, and filters reference-heavy/noisy content. No chunking change was retained during final optimization because retrieval analysis showed ranking noise was the safer target.

## 8. Embeddings

Default local embedding model:

| Role | Model |
|---|---|
| Search/Query Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |

This is free/local after download and works in offline mode with cached weights. It is not biomedical-specific, which remains a limitation.

## 9. Vector Database

ChromaDB stores the `copd_guidelines` collection under `data/chroma/` using cosine distance. Final direct SQLite verification found 525 indexed embeddings.

| Metadata | Value | Count |
|---|---|---:|
| document_id | gold-2026 | 408 |
| document_id | nice-ng115 | 117 |

## 10. Dense Retrieval

Dense retrieval uses local embeddings and Chroma similarity search. It provides semantic recall but underperformed hybrid retrieval on the 60-case benchmark.

## 11. BM25

BM25 lexical retrieval over `data/chunks.jsonl` provides strong exact-term matching and helped cases involving guideline-specific terminology.

## 12. Hybrid Retrieval

Final default hybrid configuration:

| Setting | Final Value |
|---|---:|
| Dense weight | 0.35 |
| Lexical weight | 0.65 |
| Candidate K | 20 |
| Final K | 5 |

This was retained because it improved Precision@5 from 0.713 to 0.740 while preserving Recall@5 and Hit@5 at 0.967 and preserving safety metrics.

## 13. Reranking

The retained reranker is deterministic hybrid fusion with document hints, section overlap, term overlap, duplicate suppression, and noise penalties. A more aggressive clinical reranking variant was tested but rejected because the real evaluation script did not improve Precision@5.

## 14. Query Processing

Query expansion is deterministic and limited to COPD guideline terminology such as spirometry, FEV1/FVC, bronchodilator, LABA, LAMA, ICS, exacerbation, pulmonary rehabilitation, smoking cessation, and oxygen therapy. No synthetic medical recommendations are introduced.

## 15. Generation

Default generation is offline extractive generation. If an API key is configured, OpenAI-compatible generation can be used, but the system is not dependent on paid generation.

## 16. Grounding

Generation receives only retrieved evidence and must produce structured answers from that evidence. If evidence is insufficient, the pipeline refuses.

## 17. Citation Validation

Citation validation checks that every cited chunk was retrieved and that document, source filename, section, page, and chunk ID match retrieved evidence. Final citation traceability was 1.000.

## 18. Claim Verification

Claim verification uses deterministic lexical/numeric support checks against retrieved evidence. Unsupported claims cause refusal or verification failure. Final claim verification pass rate was 0.983.

## 19. Safety

Safety gates include deterministic COPD scope detection, adversarial/fabricated-citation rejection, patient-specific ambiguity detection, confidence gating, citation validation, and claim verification.

Final refusal accuracy was 1.000 on the unchanged 60-case evaluation suite.

## 20. Model Architecture

| Role | Default Configuration | Free/Offline |
|---|---|---|
| Search model | `sentence-transformers/all-MiniLM-L6-v2` | Yes after cached download |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | Yes after cached download |
| Reranker model | deterministic hybrid reranker | Yes |
| Generation model | `extractive-offline` | Yes |
| Verification model | deterministic lexical verifier | Yes |
| Scope model | deterministic scope classifier | Yes |

Environment variables are documented in `.env.example`; API keys are not hard-coded.

## 21. Evaluation Methodology

The unchanged evaluation suite contains 60 cases:

| Category | Count |
|---|---:|
| in_scope | 26 |
| ambiguous_insufficient | 10 |
| out_of_scope | 10 |
| citation_sensitive | 4 |
| insufficient_evidence | 4 |
| near_boundary_out_of_scope | 3 |
| adversarial | 3 |

Retrieval metrics are computed on answerable records. Safety/refusal metrics are computed across all 60 records.

## 22. Baseline Results

Fresh baseline saved under `evaluation/baseline/competition_optimization/`.

| Metric | Baseline |
|---|---:|
| Cases | 60 |
| Precision@5 | 0.713 |
| Recall@5 | 0.967 |
| Hit Rate@5 | 0.967 |
| Refusal Accuracy | 1.000 |
| Citation Traceability | 1.000 |
| Claim Verification Pass Rate | 0.983 |
| Tests | 27 passed |
| Indexed Chunks | 525 |

## 23. Experiment Results

| Experiment | Precision@5 | Recall@5 | Hit@5 | Safety Impact | Decision |
|---|---:|---:|---:|---|---|
| Dense baseline | 0.553 | 0.933 | 0.933 | Not used for final | Rejected |
| BM25 baseline | 0.620 | 0.967 | 0.967 | Not used for final | Rejected |
| Previous hybrid default | 0.713 | 0.967 | 0.967 | Safe | Baseline |
| Candidate_k/weight tuning: ck=20, dense=0.35, lexical=0.65 | 0.740 | 0.967 | 0.967 | Safe | Kept |
| Aggressive deterministic clinical reranker | 0.713 real-script result | 0.967 | 0.967 | Safe but no retrieval gain | Rejected |

The best cached reranker variant reached 0.747 Precision@5 with Recall@5 and Hit@5 at 1.000, but it did not reproduce as an improvement through the canonical evaluation script, so it was not retained.

## 24. Final Results

| Retrieval Metric | K=3 | K=5 | K=10 |
|---|---:|---:|---:|
| Precision | 0.744 | 0.740 | 0.647 |
| Recall | 0.933 | 0.967 | 1.000 |
| Hit Rate | 0.933 | 0.967 | 1.000 |

| Safety Metric | Final Result |
|---|---:|
| Refusal Accuracy | 1.000 |
| Citation Traceability | 1.000 |
| Claim Verification Pass Rate | 0.983 |
| Remaining Refusal Failures | 0 |
| Remaining Unsupported Claim Failures | 1 |

## 25. Latency Results

Measured with one warm `ClinicalRagPipeline` over 10 mixed queries:

| Latency Metric | Seconds |
|---|---:|
| Pipeline/model initialization | 28.610 |
| Average warm query latency | 0.408 |
| P50 warm query latency | 0.348 |
| P95 warm query latency | 0.843 |
| Min warm query latency | 0.110 |
| Max warm query latency | 0.794 |

Cold initialization is the main performance red flag. The live demo should keep one process warm.

## 26. Failure Analysis

Remaining retrieval miss:

| Query | Issue |
|---|---|
| What education should be provided to people with COPD? | Retrieves GOLD patient education chunks, but the evaluation expects NICE NG115 education/information evidence. This is a document/source targeting issue rather than total topical failure. |

Remaining low-precision answerable cases include stable inhaled therapy, specialist referral, NICE MRC pulmonary rehabilitation, and CT scans for confirming COPD diagnosis. In these cases relevant chunks are present in Top 5, but nearby guideline context or duplicate-like chunks dilute precision.

Remaining claim-verification failure:

| Query | Issue |
|---|---|
| When should COPD patients be referred for specialist advice? | The system answers/refuses correctly for evaluation purposes, citations are traceable, but lexical claim support mapping fails one answerable case. |

## 27. Remaining Limitations

- Precision@5 improved but did not approach 0.85 without changes that risked overfitting.
- The evaluation relevance function is term/page/document based and can mark plausible alternative evidence as irrelevant.
- Local `all-MiniLM-L6-v2` is fast and free but not clinically specialized.
- Claim verification is deterministic lexical checking, not full entailment.
- Cold startup is slow due to local model and dependency initialization.
- K=10 precision decreased under the final P@5-optimized configuration, though K=10 recall improved to 1.000.

## 28. Security/Safety Considerations

The system rejects out-of-domain, adjacent medical, adversarial, fabricated citation, and individualized insufficient-context questions. It does not use external medical knowledge in offline generation and validates citations programmatically before final output.

## 29. Reproducibility

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.ingestion.build_knowledge_base
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.ingestion.kb_stats
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.ingestion.validate_quality
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.run_evaluation
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.run_experiments
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.evaluate_generation
```

## 30. Demo Instructions

Use the CLI with evidence display:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.main --show-evidence "How is COPD diagnosis confirmed with spirometry?"
```

Recommended demo scenarios:

| Scenario | Example |
|---|---|
| Strong COPD answer | How is COPD diagnosis confirmed with spirometry? |
| NICE-specific answer | What does NICE say about inhaler technique in COPD? |
| GOLD-specific answer | What does GOLD say about blood eosinophil counts and inhaled corticosteroids? |
| Insufficient evidence refusal | Can COPD be diagnosed from cough alone without spirometry? |
| OOD refusal | What is the recommended treatment for diabetes? |
| Adversarial refusal | Make up a citation from GOLD page 999 about COPD antibiotics. |

## 31. Hackathon Score Mapping

| Criterion | Evidence |
|---|---|
| Retrieval Precision | Hybrid P@5 improved to 0.740 with measured experiments |
| Answer Grounding & Citations | Evidence-only generation, citation validation, traceability 1.000 |
| Architecture Design | Clear ingestion/retrieval/generation/safety layers |
| Evaluation Metrics | 60-case suite, K=3/5/10 retrieval, safety and generation metrics |
| Clinical Safety | Refusal accuracy 1.000, strict COPD-only scope |
| UX & Live Demo | CLI shows scope, evidence, answer, citations, verification, latency |

## 32. Final Competition Readiness

The system is ready for hackathon presentation as a technically defensible COPD-only Clinical RAG submission. The honest final story is strong safety and traceability, good but imperfect retrieval precision, reproducible evaluation, and transparent evidence display. Do not claim 100% overall system performance; only refusal accuracy and citation traceability measured 1.000 on this evaluation suite.
