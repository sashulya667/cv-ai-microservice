import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.cv_review.schemas import (
    CVComparisonResponse,
    CVReviewRequest,
    CVReviewResponse,
)
from app.features.cv_review.service import CVReviewService

router = APIRouter(tags=["cv"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


@router.post("/cv/review")
async def review_cv(
    request: Request,
    payload: CVReviewRequest,
) -> CVReviewResponse | CVComparisonResponse:
    settings: Settings = request.app.state.settings

    logger.info(
        "CV review request received",
        extra={"mode": "comparison" if payload.is_comparison else "single"},
    )

    llm = LLMRegistry(settings).get(settings.llm_provider)
    service = CVReviewService(settings=settings, llm=llm)
    result = await service.review(payload=payload)

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
            extra={"overall_score": result.overall_score},
        )

    return result
