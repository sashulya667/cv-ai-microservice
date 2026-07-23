import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.cover_letter.schemas import CoverLetterRequest, CoverLetterResponse
from app.features.cover_letter.service import CoverLetterService

router = APIRouter(tags=["cover-letter"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def cover_letter(
    request: Request,
    payload: CoverLetterRequest,
) -> CoverLetterResponse:
    settings: Settings = request.app.state.settings

    logger.info(
        "Cover letter request received",
        extra={
            "mode": payload.mode,
            "locale": payload.locale,
            "variants": payload.options.variants if payload.options else 1,
            "has_vacancy": payload.vacancy is not None,
            "has_brief": bool(payload.brief),
        },
    )

    llm = LLMRegistry(settings).get(settings.llm_provider)
    service = CoverLetterService(settings=settings, llm=llm)
    result = await service.generate(request=payload)

    logger.info(
        "Cover letter completed",
        extra={
            "mode": result.mode,
            "locale": result.locale,
            "variants_count": len(result.variants),
            "warnings": result.warnings,
            "char_counts": result.meta.charCounts,
        },
    )
    return result
