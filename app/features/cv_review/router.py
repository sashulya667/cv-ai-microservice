import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.cv_review.schemas import (
    CVComparisonRequest,
    CVComparisonResponse,
    CVReviewRequest,
    CVReviewResponse,
)
from app.features.cv_review.service import CVReviewService

router = APIRouter(tags=["cv"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


def _service(request: Request) -> CVReviewService:
    settings: Settings = request.app.state.settings
    llm = LLMRegistry(settings).get(settings.llm_provider)
    return CVReviewService(settings=settings, llm=llm)


@router.post("/cv/review", response_model=CVReviewResponse)
async def review_cv(
    request: Request,
    payload: CVReviewRequest,
) -> CVReviewResponse:
    logger.info("CV review request received")

    result = await _service(request).review(resume=payload.resume)

    logger.info(
        "CV review completed",
        extra={"overall_score": result.overall_score},
    )
    return result


@router.post("/cv/compare", response_model=CVComparisonResponse)
async def compare_cv(
    request: Request,
    payload: CVComparisonRequest,
) -> CVComparisonResponse:
    logger.info("CV comparison request received")

    result = await _service(request).compare(
        current=payload.currentResume,
        previous=payload.previousResume,
    )

    logger.info(
        "CV comparison completed",
        extra={
            "delta_overall": result.delta_overall,
            "delta_ats": result.delta_ats,
            "current_score": result.current_overall_score,
        },
    )
    return result
