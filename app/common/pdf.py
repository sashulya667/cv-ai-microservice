from io import BytesIO

from pypdf import PdfReader

from app.common.errors import BadRequest


def extract_text_from_pdf(pdf_bytes: bytes, *, max_pages: int) -> str:
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as e:
        raise BadRequest(f"Invalid PDF: {e}") from e

    pages = reader.pages[:max_pages]
    chunks: list[str] = []

    for p in pages:
        try:
            chunks.append(p.extract_text() or "")
        except Exception:
            chunks.append("")

    text = "\n".join(chunks).strip()
    if not text:
        raise BadRequest(
            "Could not extract text from the PDF. If the CV is scanned, add OCR as a separate feature/module."
        )
    return text
