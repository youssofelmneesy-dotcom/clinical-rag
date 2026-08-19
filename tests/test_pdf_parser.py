from pathlib import Path

import pytest

from backend.ingestion.pdf_parser import extract_text_from_pdf


def test_pdf_parser_rejects_missing_pdf(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(str(tmp_path / "missing.pdf"))
