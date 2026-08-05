import asyncio
import logging
from urllib.parse import urlparse

import httpx

from app.common.errors import BadRequest

logger = logging.getLogger(__name__)

_PDF_MAGIC = b"%PDF"
_REJECT_CONTENT_TYPES = (
    "text/html",
    "text/plain",
    "image/",
    "audio/",
    "video/",
    "application/json",
    "application/xml",
    "text/xml",
)


def _looks_like_pdf_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


def _is_rejected_content_type(content_type: str) -> bool:
    ct = content_type.lower().split(";")[0].strip()
    if not ct or ct in ("application/octet-stream", "binary/octet-stream"):
        return False
    if "application/pdf" in ct:
        return False
    return any(ct.startswith(prefix) or ct == prefix.rstrip("/") for prefix in _REJECT_CONTENT_TYPES)


def _ensure_pdf_bytes(content: bytes, *, content_type: str, url: str) -> None:
    if content.startswith(_PDF_MAGIC):
        return
    if "application/pdf" in content_type.lower() or _looks_like_pdf_url(url):
        raise BadRequest("Файл повреждён или не является валидным PDF")
    raise BadRequest(
        f"Файл по URL не является PDF. Content-Type: {content_type or 'unknown'}"
    )


async def download_file_from_url(
    url: str,
    *,
    timeout: int = 30,
    max_size_mb: int = 10,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> bytes:
    if not url or not url.strip():
        raise BadRequest("fileUrl пустой")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise BadRequest("fileUrl должен быть публичным http(s) URL")

    max_size = max_size_mb * 1024 * 1024
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            logger.info(
                "Downloading file from URL",
                extra={"url": url, "attempt": attempt + 1, "max_retries": max_retries},
            )

            timeout_cfg = httpx.Timeout(float(timeout), connect=min(10.0, float(timeout)))
            async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code >= 400:
                        status_code = response.status_code
                        if 400 <= status_code < 500:
                            raise BadRequest(f"Не удалось загрузить файл: HTTP {status_code}")
                        raise httpx.HTTPStatusError(
                            f"HTTP {status_code}",
                            request=response.request,
                            response=response,
                        )

                    content_type = response.headers.get("content-type", "")
                    if _is_rejected_content_type(content_type):
                        raise BadRequest(
                            f"Файл по URL не является PDF. Content-Type: {content_type}"
                        )

                    content_length = response.headers.get("content-length")
                    if content_length and content_length.isdigit():
                        if int(content_length) > max_size:
                            raise BadRequest(
                                f"Файл слишком большой: {content_length} байт "
                                f"(макс {max_size} байт)"
                            )

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_size:
                            raise BadRequest(
                                f"Файл слишком большой: больше {max_size} байт"
                            )
                        chunks.append(chunk)

                    content = b"".join(chunks)
                    if not content:
                        raise BadRequest("Файл пустой")

                    _ensure_pdf_bytes(content, content_type=content_type, url=url)
                    return content

        except BadRequest:
            raise
        except httpx.HTTPStatusError as e:
            last_error = e
            status_code = e.response.status_code if e.response is not None else 0
            if 400 <= status_code < 500:
                raise BadRequest(f"Не удалось загрузить файл: HTTP {status_code}") from e
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff_factor * (2**attempt))
                continue
            raise BadRequest(
                f"Не удалось загрузить файл после {max_retries} попыток: HTTP {status_code}"
            ) from e
        except (httpx.TimeoutException, httpx.RequestError) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff_factor * (2**attempt))
                continue
            raise BadRequest(f"Ошибка при загрузке файла: {e}") from e

    raise BadRequest(f"Ошибка при загрузке файла: {last_error}")
