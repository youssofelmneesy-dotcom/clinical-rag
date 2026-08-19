from __future__ import annotations

import json
from pathlib import Path

from backend.config import CHUNKS_PATH, ChunkingConfig, VALID_SOURCE_DOCUMENTS, SourceDocument
from backend.ingestion.chunker import chunk_pages
from backend.ingestion.pdf_parser import extract_text_from_pdf
from backend.models import Chunk


def build_chunks(
    sources: tuple[SourceDocument, ...] = VALID_SOURCE_DOCUMENTS,
    output_path: Path = CHUNKS_PATH,
    chunking_config: ChunkingConfig | None = None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for source in sources:
        pages = extract_text_from_pdf(str(source.path))
        chunks.extend(chunk_pages(pages, source, chunking_config))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_json(), ensure_ascii=False, sort_keys=True) + "\n")
    return chunks


def load_chunks(chunks_path: Path = CHUNKS_PATH) -> list[Chunk]:
    chunks: list[Chunk] = []
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(Chunk(**json.loads(line)))
    return chunks
