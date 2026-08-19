# Final Status

## Verdict

Ready for hackathon presentation with an honest caveat: retrieval Precision@5 improved but did not reach the aspirational >0.85 target.

## Final Scorecard

| Metric | Final |
|---|---:|
| Evaluation cases | 60 |
| Precision@5 | 0.740 |
| Recall@5 | 0.967 |
| Hit Rate@5 | 0.967 |
| Refusal Accuracy | 1.000 |
| Citation Traceability | 1.000 |
| Claim Verification Pass Rate | 0.983 |
| P50 warm latency | 0.348 s |
| P95 warm latency | 0.843 s |
| Tests | 27 passed |
| Indexed chunks | 525 |
| Duplicate chunk IDs | 0 |
| Approved sources | 2 |

## Best Retrieval Configuration

Hybrid dense + BM25 retrieval with deterministic reranking:

- Dense weight: 0.35
- Lexical weight: 0.65
- Candidate K: 20
- Final K: 5

## Best Model Configuration

| Role | Model |
|---|---|
| Search/embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Reranking | deterministic hybrid reranker |
| Generation | `extractive-offline` |
| Verification | deterministic lexical verifier |
| Scope | deterministic COPD scope classifier |

## Improvements Kept

- Safety scope and ambiguity rules improved refusal accuracy to 1.000 on the unchanged 60-case suite.
- Hybrid retrieval default changed from dense-heavy candidate_k 30 to lexical-heavy candidate_k 20.
- Precision@5 improved from 0.713 to 0.740 without reducing Recall@5, Hit@5, citation traceability, or claim verification.

## Experiments Rejected

- Aggressive deterministic clinical reranking: rejected because the canonical retrieval evaluation did not improve Precision@5.
- Larger candidate pools: rejected because they did not improve Precision@5 enough and increased retrieval cost.
- Chunking changes: not attempted because failure analysis pointed to ranking/source-targeting noise, not ingestion integrity.

## Remaining Red Flags

- Precision@5 remains below the aspirational 0.85 target.
- One answerable retrieval miss remains for a NICE-specific education expectation.
- One claim-verification support-mapping failure remains for specialist referral advice.
- Cold pipeline initialization was measured at 28.610 s; keep the demo process warm.

## Mentor Message

The system is defensible because it preserves safety, grounding, source whitelisting, deterministic ingestion, and reproducible metrics. The honest improvement is a modest retrieval precision gain with no safety regression, not a forced 100% claim.
