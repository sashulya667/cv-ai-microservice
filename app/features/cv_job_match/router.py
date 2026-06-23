import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.cv_job_match.schemas import CVJobMatchRequest, CVJobMatchResponse
from app.features.cv_job_match.service import CVJobMatchService

router = APIRouter(tags=["cv"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


@router.post("/cv/job-match", response_model=CVJobMatchResponse)
async def cv_job_match(
    request: Request,
    payload: CVJobMatchRequest,
) -> CVJobMatchResponse:
    settings: Settings = request.app.state.settings

    logger.info("CV job match request received")

    llm = LLMRegistry(settings).get(settings.llm_provider)
    service = CVJobMatchService(settings=settings, llm=llm)
    result = await service.match(resume=payload.resume, vacancy=payload.vacancy)

    logger.info(
        "CV job match completed",
        extra={
            "match_score": result.match_score,
            "overall_fit": result.overall_fit,
            "salary_match": result.logistics_match.salary_match,
            "location_match": result.logistics_match.location_match,
        },
    )

    return result
