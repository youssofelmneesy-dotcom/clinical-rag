from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.config import EVALUATION_DIR, VALID_SOURCE_DOCUMENTS
from backend.ingestion.pdf_parser import extract_text_from_pdf


PDF_QUALITY_REPORT_PATH = EVALUATION_DIR / "pdf_quality_report.json"


def validate_pdf_quality() -> dict:
    report = {"documents": []}
    for source in VALID_SOURCE_DOCUMENTS:
        pages = extract_text_from_pdf(str(source.path))
        empty_pages = [page["page"] for page in pages if not page["text"].strip()]
        sampled_pages = _sample_pages(pages)
        report["documents"].append(
            {
                "document_id": source.document_id,
                "document_name": source.document_name,
                "source_filename": source.filename,
                "sha256": _sha256(source.path),
                "page_count": len(pages),
                "empty_pages": empty_pages,
                "sampled_pages": sampled_pages,
                "notes": _notes(sampled_pages, empty_pages),
            }
        )
    PDF_QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PDF_QUALITY_REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _sample_pages(pages: list[dict]) -> list[dict]:
    if not pages:
        return []
    indexes = sorted({0, min(4, len(pages) - 1), len(pages) // 2, len(pages) - 1})
    samples = []
    for index in indexes:
        text = pages[index]["text"]
        samples.append(
            {
                "page": pages[index]["page"],
                "char_count": len(text),
                "line_count": len(text.splitlines()),
                "preview": text[:500],
            }
        )
    return samples


def _notes(sampled_pages: list[dict], empty_pages: list[int]) -> list[str]:
    notes = []
    if empty_pages:
        notes.append(f"Empty pages detected: {empty_pages}")
    if any("copyright material - do not copy or distribute" in sample["preview"].lower() for sample in sampled_pages):
        notes.append("Repeated GOLD copyright/footer text appears in extracted text and is filtered during chunking.")
    if any("all rights reserved" in sample["preview"].lower() for sample in sampled_pages):
        notes.append("NICE rights/footer text appears in extracted text and is filtered as retrieval noise where possible.")
    if not notes:
        notes.append("Representative sampled pages contained extractable text.")
    return notes


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    report = validate_pdf_quality()
    for document in report["documents"]:
        print(
            f"{document['document_id']}: pages={document['page_count']} "
            f"empty_pages={len(document['empty_pages'])} sha256={document['sha256'][:12]}"
        )


if __name__ == "__main__":
    main()
