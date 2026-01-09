from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorResponse:
    error: str
    detail: str


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
    async def handle_bad_request(_: Request, exc: BadRequest) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "detail": exc.message},
        )

    @app.exception_handler(UpstreamError)
    async def handle_upstream(_: Request, exc: UpstreamError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"error": "upstream_error", "detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": "Unexpected server error."},
        )
