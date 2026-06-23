import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.candidate_rank.schemas import CandidateRankRequest, CandidateRankResponse
from app.features.candidate_rank.service import CandidateRankService

router = APIRouter(prefix="/employer", tags=["employer"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


@router.post("/candidate-rank", response_model=CandidateRankResponse)
async def candidate_rank(
    request: Request,
    payload: CandidateRankRequest,
) -> CandidateRankResponse:
    settings: Settings = request.app.state.settings

    logger.info(
        "Candidate rank request received",
        extra={"candidates_count": len(payload.candidates)},
    )

    llm = LLMRegistry(settings).get(settings.llm_provider)
    service = CandidateRankService(settings=settings, llm=llm)
    result = await service.rank(payload=payload)

    logger.info(
        "Candidate rank completed",
        extra={"ranked_count": len(result.ranked_candidates)},
    )

    return result
