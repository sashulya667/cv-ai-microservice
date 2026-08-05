import logging

from fastapi import APIRouter, Depends, Request

from app.ai.registry import LLMRegistry
from app.common.dependencies import rate_limit
from app.config import Settings
from app.features.resume_import.schemas import ResumeImportRequest, ResumeImportResponse
from app.features.resume_import.service import ResumeImportService

router = APIRouter(tags=["cv"], dependencies=[Depends(rate_limit)])
logger = logging.getLogger(__name__)


def _service(request: Request) -> ResumeImportService:
    settings: Settings = request.app.state.settings
    llm = LLMRegistry(settings).get(settings.llm_provider)
    return ResumeImportService(settings=settings, llm=llm)


@router.post("/cv/parse-resume", response_model=ResumeImportResponse)
async def parse_resume(
    request: Request,
    payload: ResumeImportRequest,
) -> ResumeImportResponse:
    logger.info(
        "Resume import request received",
        extra={"file_key": payload.fileKey},
    )

    result = await _service(request).parse(request=payload)

    logger.info(
        "Resume import completed",
        extra={
            "file_key": payload.fileKey,
            "experiences": len(result.workExperiences),
            "education": len(result.education),
            "skills": len(result.skills),
            "warnings": result.warnings,
        },
    )
    return result
