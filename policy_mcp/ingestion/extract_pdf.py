from pathlib import Path

from pypdf import PdfReader


PDF_PATH = (
    Path(__file__).resolve().parent.parent
    / "documents"
    / "return_policy_de_2026.pdf"
)


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if not text:
            continue

        pages.append(
            f"\n--- PAGE {page_number} ---\n{text.strip()}"
        )

    return "\n".join(pages)


if __name__ == "__main__":
    text = extract_pdf_text(PDF_PATH)

    print(text)