# Загрузка файлов по URL временно отключена — входные данные принимаются в структурированном JSON-формате.
# Оставлен для возможного восстановления в будущем.
#
# import asyncio
# import logging
#
# import httpx
#
# from app.common.errors import BadRequest
#
# logger = logging.getLogger(__name__)
#
#
# async def download_file_from_url(
#     url: str,
#     *,
#     timeout: int = 30,
#     max_size_mb: int = 10,
#     max_retries: int = 3,
#     backoff_factor: float = 0.5,
# ) -> bytes:
#     max_size = max_size_mb * 1024 * 1024
#
#     for attempt in range(max_retries):
#         try:
#             logger.info(
#                 "Downloading file from URL",
#                 extra={"url": url, "attempt": attempt + 1, "max_retries": max_retries},
#             )
#
#             async with httpx.AsyncClient(timeout=timeout) as client:
#                 response = await client.get(url, follow_redirects=True)
#                 response.raise_for_status()
#
#                 content_type = response.headers.get("content-type", "")
#                 if "application/pdf" not in content_type.lower():
#                     raise BadRequest(f"Файл по URL не является PDF. Content-Type: {content_type}")
#
#                 content = response.content
#                 if not content:
#                     raise BadRequest("Файл пустой")
#
#                 if len(content) > max_size:
#                     raise BadRequest(
#                         f"Файл слишком большой: {len(content)} байт (макс {max_size} байт)"
#                     )
#
#                 return content
#
#         except httpx.HTTPStatusError as e:
#             status_code = e.response.status_code
#             if 400 <= status_code < 500:
#                 raise BadRequest(f"Не удалось загрузить файл: HTTP {status_code}") from e
#             if attempt < max_retries - 1:
#                 await asyncio.sleep(backoff_factor * (2**attempt))
#                 continue
#             raise BadRequest(
#                 f"Не удалось загрузить файл после {max_retries} попыток: HTTP {status_code}"
#             ) from e
#
#         except (httpx.TimeoutException, httpx.RequestError) as e:
#             if attempt < max_retries - 1:
#                 await asyncio.sleep(backoff_factor * (2**attempt))
#                 continue
#             raise BadRequest(f"Ошибка при загрузке файла: {e}") from e
#
#     raise BadRequest("Неизвестная ошибка при загрузке файла")
