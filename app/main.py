from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.errors import install_exception_handlers
from app.common.logging import configure_logging
from app.common.middleware import RequestContextMiddleware
from app.common.rate_limiter import RateLimiter
from app.config import Settings
from app.features.cv_review.router import router as cv_review_router
from app.features.health.router import router as health_router
from app.features.cv_job_match.router import router as cv_job_match_router


def create_app() -> FastAPI:
    settings = Settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )
    app.state.settings = settings

    if settings.rate_limit_enabled:
        rate_limiter = RateLimiter(requests_per_hour=settings.rate_limit_per_hour)
        app.state.rate_limiter = rate_limiter

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(RequestContextMiddleware)

    install_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(cv_review_router)
    app.include_router(cv_job_match_router)

    return app
