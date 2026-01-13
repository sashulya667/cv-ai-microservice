from fastapi import APIRouter, Request

from app.ai.base import LLMFile
from app.ai.registry import LLMRegistry
from app.common.errors import BadRequest
from app.common.http_client import download_file_from_url
from app.config import Settings
from app.features.cv_review.schemas import (
    CVComparisonResponse,
    CVReviewRequest,
    CVReviewResponse,
)
from app.features.cv_review.service import CVReviewService
import logging

router = APIRouter(tags=["cv"])
logger = logging.getLogger(__name__)


@router.post("/cv/review")
async def review_cv(
    request: Request,
    payload: CVReviewRequest,
) -> CVReviewResponse | CVComparisonResponse:
    settings: Settings = request.app.state.settings

    if settings.rate_limit_enabled and hasattr(request.app.state, "rate_limiter"):
        request.app.state.rate_limiter.check_limit(request)

    logger.info(
        "CV review request received",
        extra={"cv_count": len(payload.cv_urls)},
    )

    if not payload.cv_urls or len(payload.cv_urls) < 1:
        raise BadRequest("Нужно передать минимум 1 URL на CV (PDF).")

    if len(payload.cv_urls) > 2:
        raise BadRequest("Можно передать максимум 2 URL: текущий CV и предыдущий CV.")

    llm_files: list[LLMFile] = []
    for i, url in enumerate(payload.cv_urls, start=1):
        file_bytes = await download_file_from_url(
            str(url),
            timeout=settings.http_timeout,
            max_size_mb=settings.http_max_file_size_mb,
            max_retries=settings.http_retry_attempts,
            backoff_factor=settings.http_retry_backoff_factor,
        )

        llm_files.append(
            LLMFile(
                filename=f"cv_{i}.pdf",
                mime_type="application/pdf",
                content=file_bytes,
            )
        )

    provider = settings.llm_provider
    llm = LLMRegistry(settings).get(provider)

    service = CVReviewService(settings=settings, llm=llm)

    result = await service.review(files=llm_files)
    
    if isinstance(result, CVComparisonResponse):
        logger.info(
            "CV comparison completed",
            extra={
                "delta_overall": result.delta_overall,
                "delta_ats": result.delta_ats,
                "current_score": result.current_overall_score,
            },
        )
    else:
        logger.info(
            "CV review completed",
            extra={
                "cv_count": len(payload.cv_urls),
                "overall_score": result.overall_score,
            },
        )
    
    return result