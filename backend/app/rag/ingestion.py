from pathlib import Path
import fitz


DOCUMENTS_DIR = Path("/srv/ai-data/documents")


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from all pages of a PDF."""
    text_parts = []

    with fitz.open(pdf_path) as document:
        for page in document:
            text_parts.append(page.get_text())

    return "\n".join(text_parts).strip()


def ingest_documents() -> dict:
    """Extract text from all PDFs in the documents directory."""
    pdf_files = sorted(DOCUMENTS_DIR.glob("*.pdf"))

    results = []

    for pdf_path in pdf_files:
        text = extract_pdf_text(pdf_path)

        results.append(
            {
                "filename": pdf_path.name,
                "characters": len(text),
                "pages": len(fitz.open(pdf_path)),
            }
        )

    return {
        "documents_found": len(pdf_files),
        "documents": results,
    }
