import json
from typing import Type, TypeVar

from pydantic import BaseModel

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.cv_review import compare_user_prompt, review_user_prompt, system_prompt
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.cv_review.schemas import CVComparisonResponse, CVReviewResponse
from app.features.shared.schemas import Resume

T = TypeVar("T", bound=BaseModel)


def _resume_to_json(resume: Resume) -> str:
    return json.dumps(resume.model_dump(exclude_none=True), ensure_ascii=False, indent=2)


class CVReviewService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def review(self, *, resume: Resume) -> CVReviewResponse:
        return await self._generate(
            user=review_user_prompt(resume_json=_resume_to_json(resume)),
            schema=CVReviewResponse,
        )

    async def compare(self, *, current: Resume, previous: Resume) -> CVComparisonResponse:
        return await self._generate(
            user=compare_user_prompt(
                current_resume_json=_resume_to_json(current),
                previous_resume_json=_resume_to_json(previous),
            ),
            schema=CVComparisonResponse,
        )

    async def _generate(self, *, user: str, schema: Type[T]) -> T:
        resp = await self.llm.generate(
            inp=LLMInput(system=system_prompt("v1"), user=user)
        )
        return parse_model_output(text=resp.text, schema=schema)
