import asyncio
import logging

import httpx

from app.common.errors import BadRequest

logger = logging.getLogger(__name__)


async def download_file_from_url(
    url: str,
    *,
    timeout: int = 30,
    max_size_mb: int = 10,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> bytes:
    max_size = max_size_mb * 1024 * 1024
    
    for attempt in range(max_retries):
        try:
            logger.info(
                "Downloading file from URL",
                extra={
                    "url": url,
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                },
            )
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                if "application/pdf" not in content_type.lower():
                    logger.error(
                        "Invalid content type",
                        extra={"url": url, "content_type": content_type},
                    )
                    raise BadRequest(
                        f"Файл по URL не является PDF. Content-Type: {content_type}"
                    )
                
                content = response.content
                if not content:
                    logger.error("Empty file content", extra={"url": url})
                    raise BadRequest("Файл пустой")
                    
                if len(content) > max_size:
                    logger.error(
                        "File too large",
                        extra={
                            "url": url,
                            "size": len(content),
                            "max_size": max_size,
                        },
                    )
                    raise BadRequest(
                        f"Файл слишком большой: {len(content)} байт (макс {max_size} байт)"
                    )
                
                logger.info(
                    "File downloaded successfully",
                    extra={"url": url, "size": len(content)},
                )
                return content
                
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            if 400 <= status_code < 500:
                logger.error(
                    "HTTP client error (no retry)",
                    extra={"url": url, "status_code": status_code},
                )
                raise BadRequest(
                    f"Не удалось загрузить файл: HTTP {status_code}"
                ) from e
            
            if attempt < max_retries - 1:
                wait_time = backoff_factor * (2**attempt)
                logger.warning(
                    "HTTP server error, retrying",
                    extra={
                        "url": url,
                        "status_code": status_code,
                        "attempt": attempt + 1,
                        "wait_time": wait_time,
                    },
                )
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(
                    "HTTP server error (max retries exceeded)",
                    extra={"url": url, "status_code": status_code},
                )
                raise BadRequest(
                    f"Не удалось загрузить файл после {max_retries} попыток: HTTP {status_code}"
                ) from e
                
        except httpx.TimeoutException as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor * (2**attempt)
                logger.warning(
                    "Timeout, retrying",
                    extra={"url": url, "attempt": attempt + 1, "wait_time": wait_time},
                )
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(
                    "Timeout (max retries exceeded)",
                    extra={"url": url},
                )
                raise BadRequest(
                    f"Превышен таймаут при загрузке файла после {max_retries} попыток"
                ) from e
                
        except httpx.RequestError as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor * (2**attempt)
                logger.warning(
                    "Request error, retrying",
                    extra={
                        "url": url,
                        "error": str(e),
                        "attempt": attempt + 1,
                        "wait_time": wait_time,
                    },
                )
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(
                    "Request error (max retries exceeded)",
                    extra={"url": url, "error": str(e)},
                )
                raise BadRequest(
                    f"Ошибка при загрузке файла после {max_retries} попыток: {str(e)}"
                ) from e
    
    raise BadRequest("Неизвестная ошибка при загрузке файла")

