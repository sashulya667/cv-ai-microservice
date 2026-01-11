from fastapi import APIRouter, Request

from app.ai.base import LLMFile
from app.ai.registry import LLMRegistry
from app.common.errors import BadRequest
from app.common.http_client import download_file_from_url
from app.config import Settings
from app.features.cv_job_match.schemas import CVJobMatchRequest, CVJobMatchResponse
from app.features.cv_job_match.service import CVJobMatchService
import logging

router = APIRouter(tags=["cv"])
logger = logging.getLogger(__name__)


@router.post("/cv/job-match", response_model=CVJobMatchResponse)
async def cv_job_match(
    request: Request,
    payload: CVJobMatchRequest,
) -> CVJobMatchResponse:
    settings: Settings = request.app.state.settings

    if settings.rate_limit_enabled and hasattr(request.app.state, "rate_limiter"):
        request.app.state.rate_limiter.check_limit(request)

    logger.info(
        "CV job match request received",
        extra={"cv_url": str(payload.cv_url)},
    )

    if not payload.job_description or not payload.job_description.strip():
        raise BadRequest("job_description must be a non-empty string.")

    cv_bytes = await download_file_from_url(
        str(payload.cv_url),
        timeout=settings.http_timeout,
        max_size_mb=settings.http_max_file_size_mb,
        max_retries=settings.http_retry_attempts,
        backoff_factor=settings.http_retry_backoff_factor,
    )

    provider = settings.llm_provider
    llm = LLMRegistry(settings).get(provider)

    service = CVJobMatchService(settings=settings, llm=llm)

    result = await service.match(
        job_description=payload.job_description,
        files=[
            LLMFile(
                filename="cv.pdf",
                mime_type="application/pdf",
                content=cv_bytes,
            )
        ],
    )
    
    logger.info(
        "CV job match completed",
        extra={
            "cv_url": str(payload.cv_url),
            "match_score": result.match_score,
            "overall_fit": result.overall_fit,
        },
    )
    
    return result
