import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.profile_boost.schemas import ProfileBoostRequest, ProfileBoostResponse
from app.features.profile_boost.service import ProfileBoostService

router = APIRouter(tags=["profile"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


@router.post("/profile-boost", response_model=ProfileBoostResponse)
async def profile_boost(
    request: Request,
    payload: ProfileBoostRequest,
) -> ProfileBoostResponse:
    settings: Settings = request.app.state.settings

    logger.info(
        "Profile boost request received",
        extra={
            "target": payload.target,
            "mode": payload.mode,
            "variants": payload.options.variants if payload.options else 1,
        },
    )

    llm = LLMRegistry(settings).get(settings.llm_provider)
    service = ProfileBoostService(settings=settings, llm=llm)
    result = await service.boost(request=payload)

    logger.info(
        "Profile boost completed",
        extra={
            "target": result.target,
            "mode": result.mode,
            "variants_count": len(result.variants),
            "warnings": result.warnings,
        },
    )
    return result
