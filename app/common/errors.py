from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.middleware import request_id_var

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorResponse:
    error: str
    detail: str
    request_id: str | None = None


class AppError(Exception):
    pass


class BadRequest(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UpstreamError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BadRequest)
    async def handle_bad_request(request: Request, exc: BadRequest) -> JSONResponse:
        request_id = request_id_var.get("")
        logger.warning(
            "Bad request",
            extra={"request_id": request_id, "error": exc.message},
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "bad_request",
                "detail": exc.message,
                "request_id": request_id or None,
            },
        )

    @app.exception_handler(UpstreamError)
    async def handle_upstream(request: Request, exc: UpstreamError) -> JSONResponse:
        request_id = request_id_var.get("")
        logger.error(
            "Upstream error",
            extra={"request_id": request_id, "error": exc.message},
        )
        return JSONResponse(
            status_code=502,
            content={
                "error": "upstream_error",
                "detail": exc.message,
                "request_id": request_id or None,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = request_id_var.get("")
        logger.exception(
            "Unhandled exception",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "detail": "Unexpected server error.",
                "request_id": request_id or None,
            },
        )
