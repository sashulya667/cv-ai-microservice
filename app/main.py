from fastapi import FastAPI

from app.common.errors import install_exception_handlers
from app.common.logging import configure_logging
from app.config import Settings
from app.features.cv_review.router import router as cv_review_router
from app.features.health.router import router as health_router
from app.features.cv_job_match.router import router as cv_job_match_router


def create_app() -> FastAPI:
    settings = Settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.settings = settings

    install_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(cv_review_router)
    app.include_router(cv_job_match_router)

    return app
