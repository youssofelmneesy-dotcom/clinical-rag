from pdf_parser import extract_text_from_pdf


PDF_PATH = "../../data/guidelines/chronic-obstructive-pulmonary-disease-in-over-16s-diagnosis-and-management-pdf-66141600098245.pdf"


def main():
    pages = extract_text_from_pdf(PDF_PATH)

    print(f"Extracted {len(pages)} pages\n")

    for page in pages[:5]:
        print("=" * 80)
        print(f"PAGE {page['page']}")
        print("=" * 80)
        print(page["text"][:2000])
        print()


if __name__ == "__main__":
    main()


