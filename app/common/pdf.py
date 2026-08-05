from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.common.errors import BadRequest


def extract_text_from_pdf(pdf_bytes: bytes, *, max_pages: int) -> str:
    if not pdf_bytes:
        raise BadRequest("PDF файл пустой")
    if not pdf_bytes.startswith(b"%PDF"):
        raise BadRequest("Файл не является валидным PDF")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except PdfReadError as e:
        raise BadRequest(f"Invalid PDF: {e}") from e
    except Exception as e:
        raise BadRequest(f"Invalid PDF: {e}") from e

    if reader.is_encrypted:
        try:
            unlocked = reader.decrypt("")
        except Exception as e:
            raise BadRequest("PDF защищён паролем и не может быть прочитан") from e
        if int(unlocked) == 0:
            raise BadRequest("PDF защищён паролем и не может быть прочитан")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise BadRequest("PDF не содержит страниц")

    pages = reader.pages[: max(1, max_pages)]
    chunks: list[str] = []

    for page in pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            chunks.append("")

    text = "\n".join(chunks).strip()
    if not text:
        raise BadRequest(
            "Не удалось извлечь текст из PDF. "
            "Если резюме — скан/изображение, OCR не поддерживается."
        )
    return text
