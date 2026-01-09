from fastapi import APIRouter, File, Form, Request, UploadFile

from app.ai.base import LLMFile
from app.ai.registry import LLMRegistry
from app.common.errors import BadRequest
from app.config import Settings
from app.features.cv_job_match.schemas import CVJobMatchResponse
from app.features.cv_job_match.service import CVJobMatchService

router = APIRouter(tags=["cv"])


@router.post("/cv/job-match", response_model=CVJobMatchResponse)
async def cv_job_match(
    request: Request,
    job_description: str = Form(...),
    file: UploadFile = File(...),
) -> CVJobMatchResponse:
    settings: Settings = request.app.state.settings

    if not job_description or not job_description.strip():
        raise BadRequest("job_description must be a non-empty string.")

    cv_bytes = await file.read()

    provider = settings.llm_provider
    llm = LLMRegistry(settings).get(provider)

    service = CVJobMatchService(settings=settings, llm=llm)

    return await service.match(
        job_description=job_description,
        files=[
            LLMFile(
                filename=file.filename,
                mime_type=file.content_type,
                content=cv_bytes,
            )
        ],
    )