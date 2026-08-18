import fitz
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from every page of a PDF.

    Returns:
        A list of dictionaries containing:
        - page: 1-based page number
        - text: extracted page text
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {pdf_path.suffix}")

    pages = []

    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages

