import asyncio
import logging
from typing import Callable, TypeVar

from app.common.errors import UpstreamError

logger = logging.getLogger(__name__)

T = TypeVar("T")

_RETRYABLE_MARKERS = ("429", "503", "500", "quota", "rate limit", "overloaded", "unavailable")


def is_retryable(error: Exception) -> bool:
    msg = str(error).lower()
    return any(marker in msg for marker in _RETRYABLE_MARKERS)


async def retry_async(
    fn: Callable[[], "asyncio.Future[T]"],
    *,
    attempts: int,
    backoff_factor: float,
    operation: str = "LLM call",
) -> T:
    for attempt in range(attempts):
        try:
            return await fn()
        except UpstreamError as exc:
            is_last = attempt == attempts - 1
            if is_last or not is_retryable(exc):
                if is_last:
                    logger.error(
                        "%s failed after %d/%d attempts — last error: %s",
                        operation,
                        attempt + 1,
                        attempts,
                        exc,
                    )
                raise
            wait = backoff_factor * (2**attempt)
            logger.warning(
                "%s transient error (attempt %d/%d, retry in %.1fs): %s",
                operation,
                attempt + 1,
                attempts,
                wait,
                exc,
            )
            await asyncio.sleep(wait)

    raise UpstreamError(f"{operation} failed after {attempts} attempts")
