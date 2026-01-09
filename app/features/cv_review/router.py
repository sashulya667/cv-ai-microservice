from typing import List
from fastapi import APIRouter, File, Request, UploadFile

from app.ai.base import LLMFile
from app.ai.registry import LLMRegistry
from app.common.errors import BadRequest
from app.config import Settings
from app.features.cv_review.schemas import CVReviewResponse
from app.features.cv_review.service import CVReviewService

router = APIRouter(tags=["cv"])


@router.post("/cv/review", response_model=CVReviewResponse)
async def review_cv(
    request: Request,
    files: List[UploadFile] = File(...),
) -> CVReviewResponse:
    settings: Settings = request.app.state.settings

    if not files or len(files) < 1:
        raise BadRequest("Нужно загрузить минимум 1 файл CV (PDF).")

    if len(files) > 2:
        raise BadRequest("Можно загрузить максимум 2 файла: текущий CV и предыдущий CV.")

    llm_files: List[LLMFile] = []
    for i, f in enumerate(files, start=1):
        if f.content_type not in ("application/pdf", "application/x-pdf"):
            raise BadRequest(f"Файл #{i}: поддерживаются только PDF.")

        file_bytes = await f.read()

        llm_files.append(
            LLMFile(
                filename=f.filename or f"cv_{i}.pdf",
                mime_type=f.content_type or "application/pdf",
                content=file_bytes,
            )
        )

    provider = settings.llm_provider
    llm = LLMRegistry(settings).get(provider)

    service = CVReviewService(settings=settings, llm=llm)

    return await service.review(files=llm_files)