from fastapi import Depends, Request

from app.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def rate_limit(request: Request) -> None:
    settings: Settings = request.app.state.settings
    if not settings.rate_limit_enabled:
        return
    limiter = getattr(request.app.state, "rate_limiter", None)
    if limiter:
        limiter.check_limit(request)
