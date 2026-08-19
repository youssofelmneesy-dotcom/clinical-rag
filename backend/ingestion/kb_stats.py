from __future__ import annotations

import json
from collections import Counter

from backend.config import EVALUATION_DIR, VALID_SOURCE_DOCUMENTS
from backend.ingestion.knowledge_base import load_chunks


KB_STATS_REPORT_PATH = EVALUATION_DIR / "kb_stats.json"


def build_kb_stats() -> dict:
    chunks = load_chunks()
    valid_filenames = {source.filename for source in VALID_SOURCE_DOCUMENTS}
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    report = {
        "chunk_count": len(chunks),
        "chunks_by_document": dict(Counter(chunk.document_id for chunk in chunks)),
        "source_filenames": sorted({chunk.source_filename for chunk in chunks}),
        "duplicate_chunk_ids": sorted([chunk_id for chunk_id, count in Counter(chunk_ids).items() if count > 1]),
        "empty_chunk_count": sum(1 for chunk in chunks if not chunk.text.strip()),
        "unknown_section_count": sum(1 for chunk in chunks if chunk.section == "Unknown"),
        "whitelist_valid": all(chunk.source_filename in valid_filenames for chunk in chunks),
        "efhs_chunk_count": sum(1 for chunk in chunks if "efhs" in chunk.source_filename.lower()),
        "reference_like_chunk_count": sum(1 for chunk in chunks if chunk.section.upper() == "REFERENCES"),
    }
    KB_STATS_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with KB_STATS_REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


def main() -> None:
    report = build_kb_stats()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
