import json

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.cv_review import system_prompt, user_prompt
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.cv_review.schemas import CVComparisonResponse, CVReviewRequest, CVReviewResponse
from app.features.shared.schemas import Resume


def _resume_to_json(resume: Resume) -> str:
    return json.dumps(resume.model_dump(exclude_none=True), ensure_ascii=False, indent=2)


class CVReviewService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def review(self, *, payload: CVReviewRequest) -> CVReviewResponse | CVComparisonResponse:
        if payload.is_comparison:
            prompt = user_prompt(
                compare=True,
                current_resume_json=_resume_to_json(payload.currentResume),  # type: ignore[arg-type]
                previous_resume_json=_resume_to_json(payload.previousResume),  # type: ignore[arg-type]
            )
            schema = CVComparisonResponse
        else:
            prompt = user_prompt(
                compare=False,
                resume_json=_resume_to_json(payload.resume),  # type: ignore[arg-type]
            )
            schema = CVReviewResponse

        resp = await self.llm.generate(
            inp=LLMInput(system=system_prompt("v1"), user=prompt)
        )
        return parse_model_output(text=resp.text, schema=schema)
