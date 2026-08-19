from __future__ import annotations

import argparse

from backend.ingestion.indexer import index_chunks
from backend.ingestion.knowledge_base import build_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the whitelisted COPD knowledge base.")
    parser.add_argument("--skip-chroma", action="store_true", help="Only write data/chunks.jsonl.")
    args = parser.parse_args()

    chunks = build_chunks()
    print(f"Wrote {len(chunks)} chunks to data/chunks.jsonl")
    if not args.skip_chroma:
        count = index_chunks(chunks)
        print(f"Indexed {count} deterministic chunk ids into data/chroma/")


if __name__ == "__main__":
    main()
