import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)

        start_time = time.time()

        logger.info(
            "%s %s",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "client_ip": request.client.host if request.client else None,
            },
        )

        response = await call_next(request)

        duration = time.time() - start_time

        logger.info(
            "%s %s → %d (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration * 1000,
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        response.headers["X-Request-ID"] = request_id

        return response


class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Returns 503 immediately when active requests exceed the per-worker limit."""

    def __init__(self, app, max_concurrent: int) -> None:
        super().__init__(app)
        self._max = max_concurrent
        self._active = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path.startswith("/health"):
            return await call_next(request)

        if self._active >= self._max:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "service_unavailable",
                    "detail": "Server is overloaded. Please retry later.",
                    "request_id": request_id_var.get() or None,
                },
                headers={"Retry-After": "5"},
            )

        self._active += 1
        try:
            return await call_next(request)
        finally:
            self._active -= 1


class StructuredLogFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_id_var.get("")
        if request_id:
            record.request_id = request_id
        return True

