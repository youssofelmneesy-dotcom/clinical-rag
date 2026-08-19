# Clinical RAG MVP Report

## Final Architecture

```text
PDF parser -> section-aware chunker -> data/chunks.jsonl -> local embeddings -> ChromaDB
     -> retriever -> OOD scope check -> confidence/evidence gate -> grounded generator
     -> structured answer with citations -> claim verifier -> final answer/refusal
```

The system remains scoped to Chronic Obstructive Pulmonary Disease (COPD). Clinical evidence is limited to the whitelisted GOLD 2026 and NICE NG115 PDFs. EFHS PDFs are excluded and are not parsed, chunked, embedded, or indexed.

## Files Created

- `backend/__init__.py`: makes `backend` importable as a package.
- `backend/config.py`: central paths, whitelisted source documents, chunking, embedding, and retrieval configuration.
- `backend/models.py`: shared dataclasses for chunks, evidence, safety decisions, structured answers, and claim verification.
- `backend/embeddings.py`: local Sentence Transformers embedding service plus deterministic test embedding service.
- `backend/ingestion/__init__.py`: ingestion package marker.
- `backend/ingestion/chunker.py`: section-aware PDF page chunking with heading heuristics, paragraph grouping, overlap, deterministic IDs, footer/reference filtering.
- `backend/ingestion/knowledge_base.py`: writes and loads `data/chunks.jsonl` from the explicit GOLD/NICE whitelist.
- `backend/ingestion/indexer.py`: synchronizes chunks into ChromaDB with deterministic IDs.
- `backend/ingestion/build_knowledge_base.py`: CLI entry point for chunking and indexing.
- `backend/retrieval/__init__.py`: retrieval package marker.
- `backend/retrieval/vector_store.py`: persistent ChromaDB wrapper using cosine distance and idempotent sync.
- `backend/retrieval/retriever.py`: query embedding/search service with conservative COPD query expansion and duplicate result filtering.
- `backend/evaluation.py`: retrieval evaluation metrics and confidence-threshold calibration.
- `backend/run_evaluation.py`: CLI entry point for retrieval evaluation.
- `backend/generation/__init__.py`: generation package marker.
- `backend/generation/generator.py`: grounding prompt, optional OpenAI JSON generator, and offline extractive generator.
- `backend/safety/__init__.py`: safety package marker.
- `backend/safety/confidence.py`: calibrated evidence gate with ambiguity checks.
- `backend/safety/scope.py`: COPD-specific scope and adjacent-domain rejection.
- `backend/safety/claim_verifier.py`: MVP claim extraction and evidence support checking.
- `backend/pipeline.py`: end-to-end RAG orchestration.
- `.env.example`: optional OpenAI generation variables.
- `evaluation/retrieval_eval.jsonl`: 40-question retrieval evaluation dataset.
- `tests/*.py`: unit/integration tests for parser behavior, chunking, KB metadata, embeddings, Chroma, retrieval evaluation, generation, confidence, OOD, and claim verification.

## Files Modified

- `backend/main.py`: CLI for asking the complete COPD RAG pipeline a question.
- `backend/ingestion/test_pdf_parser.py`: preserved the manual PDF smoke script and fixed package-safe import.
- `requirements.txt`: added `chromadb`, `sentence-transformers`, `openai`, and `pytest` alongside `PyMuPDF`.
- `data/chunks.jsonl`: generated whitelisted COPD knowledge-base chunks.
- `data/chroma/`: generated persistent local ChromaDB index.
- `evaluation/retrieval_report.json`: generated final retrieval evaluation report.
- `evaluation/confidence_threshold.json`: generated calibrated confidence threshold.

## Steps 5-18 Status

- Step 5 PDF parser: existing PyMuPDF parser preserved.
- Step 6 PDF validation: existing manual script preserved.
- Step 7 Chunking: implemented section-aware chunking with document-specific heading heuristics and structural grouping.
- Step 8 Knowledge base: implemented deterministic JSONL chunks with citation metadata.
- Step 9 Embeddings: implemented local Sentence Transformers embeddings using `sentence-transformers/all-MiniLM-L6-v2`; dimension is read from the model at runtime.
- Step 10 ChromaDB: implemented persistent ChromaDB at `data/chroma/`, cosine distance, deterministic IDs, and idempotent sync.
- Step 11 Retrieval: implemented query embedding, Chroma similarity search, structured evidence results, and configurable K.
- Step 12 Dataset: implemented 40-record evaluation dataset: 20 in-scope, 10 ambiguous/insufficient, 10 out-of-scope.
- Step 13 Evaluation: implemented Precision@5, Recall@5, Hit@5, per-question top results, and threshold analysis.
- Step 14 Grounding: implemented evidence-only JSON grounding prompt; offline extractive generator is default, optional OpenAI generation uses environment variables.
- Step 15 Structured output: final answers render `Recommendation`, `Evidence`, `Sources`, and optional `Conflicting Guidance`; citations include document, source filename, section, page, and chunk ID.
- Step 16 Confidence gate: threshold is calibrated from retrieval evaluation results; final selected threshold is `0.50`.
- Step 17 OOD detection: COPD scope detector rejects non-COPD and adjacent unsafe topics before generation.
- Step 18 Claim verification: generated claims are extracted and checked against retrieved evidence; unsupported claims cause final refusal.

## PDF Parser Behavior

The existing parser in `backend/ingestion/pdf_parser.py` uses PyMuPDF, validates file existence and `.pdf` suffix, and returns 1-based page dictionaries containing extracted text. It was not rewritten.

## Chunking Strategy

Chunking follows `PDF -> page -> section/subsection -> paragraph/logical unit -> chunk`. GOLD and NICE use separate heading regexes. Uncertain sections remain `Unknown`. Chunk size defaults to 1400 characters, overlap to 180 characters, and minimum chunk size to 180 characters. The chunker avoids splitting recommendation-like units where possible and filters repeated copyright/disclaimer lines plus reference-heavy chunks.

## Embeddings

The selected model is `sentence-transformers/all-MiniLM-L6-v2`. It is local after first download, practical for a developer laptop, no paid API is required, and it is suitable for English semantic retrieval. It is not a COPD-specific biomedical model; this is a known MVP limitation. The vector dimension is determined programmatically from the model.

## ChromaDB Configuration

ChromaDB collection: `copd_guidelines`. Persistence path: `data/chroma/`. Distance metric: cosine via collection metadata `hnsw:space=cosine`. IDs are deterministic `chunk_id` values. Indexing uses sync semantics: stale IDs are removed and current whitelisted chunks are upserted.

## Retrieval Strategy

The retriever embeds the user question, applies conservative COPD query expansion for common clinical intents, queries ChromaDB, converts cosine distance to `similarity = 1 - distance`, de-duplicates near-identical text, and returns structured evidence with full metadata.

## Evaluation Dataset and Results

Final evaluation command:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.run_evaluation
```

Final results from `evaluation/retrieval_report.json`:

- Questions: 40
- Answerable records: 20
- Precision@5: 0.550
- Recall@5: 0.950
- Hit Rate@5: 0.950
- Selected threshold: 0.50
- Threshold behavior at 0.50: true accepts 19, false accepts 12, false rejects 0, true rejects 9

The threshold is not arbitrary; it was selected by the evaluation harness from candidate thresholds. OOD and ambiguity gates are still required because retrieval similarity alone produced false accepts for some unanswerable records.

## Grounding and Structured Output

The grounding prompt tells the LLM that the evidence is the source of truth, requires valid JSON, and requires source objects to cite document, source filename, section, page, and chunk ID. If `OPENAI_API_KEY` is absent, the system uses an offline extractive generator that only assembles sentences from retrieved evidence.

## OOD Detection

The scope detector combines direct COPD terms, COPD clinical-context terms, retrieved COPD evidence, and explicit non-COPD/adjacent-domain signals. Diabetes, migraine, and cancer screening/surveillance examples are rejected before generation.

## Claim Verification

The verifier extracts clinically meaningful answer sentences, checks numeric claims against evidence text, and requires exact or high-overlap support from retrieved evidence. Unsupported generated claims cause the pipeline to return the insufficient-evidence refusal.

## Tests

Final test command:

```bash
.venv/bin/python -m pytest -q
```

Final result: 20 passed, 6 warnings. Warnings came from PyMuPDF/SWIG deprecations and a Chroma telemetry deprecation under Python 3.14; no test failed.

## Ingestion and Chroma Statistics

Final ingestion command:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.ingestion.build_knowledge_base
```

Final ingestion/indexing result:

- `data/chunks.jsonl`: 525 chunks
- Chroma records: 525
- GOLD chunks: 408
- NICE chunks: 117
- Chroma document IDs: `gold-2026`, `nice-ng115`
- Chroma source filenames: `GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf`, `chronic-obstructive-pulmonary-disease-in-over-16s-diagnosis-and-management-pdf-66141600098245.pdf`
- Repeated ingestion/indexing returned 525 records again, confirming no duplicate growth.

## End-to-End Validation

Validated examples:

- In-scope: "How is COPD diagnosis confirmed with spirometry?" returned a structured answer with GOLD evidence, confidence 0.882, threshold 0.50, and supported claim verification.
- In-scope: "What is recommended about pulmonary rehabilitation in COPD?" returned GOLD and NICE evidence separately, confidence 0.795, threshold 0.50, and supported claim verification.
- Ambiguous/insufficient: "What is the best COPD inhaler for a patient with missing spirometry and no symptom history?" was refused by the evidence gate because individualized assessment details were missing.
- Out-of-scope: "What is the recommended treatment for diabetes?" was rejected before generation.
- Adjacent out-of-scope: "What screening interval is recommended for COPD lung cancer surveillance?" was rejected before generation.

## Known Limitations

- The default generator is extractive and can be verbose because it avoids unsupported synthesis when no API key is configured.
- `all-MiniLM-L6-v2` is practical and local but not COPD-specific; retrieval could improve with a clinically tuned local embedding model.
- Confidence thresholding alone has false accepts; final safety depends on combining confidence with OOD and ambiguity gates.
- Claim verification is lexical/numeric MVP checking, not full natural-language entailment.
- Optional OpenAI generation was not live-validated because no real API key was used; offline generation and parser behavior were tested.

## Run Commands

Install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Build the knowledge base:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.ingestion.build_knowledge_base
```

Evaluate retrieval:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.run_evaluation
```

Ask the complete system:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m backend.main "How is COPD diagnosis confirmed with spirometry?"
```
