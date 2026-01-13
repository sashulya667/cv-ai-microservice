from app.ai.base import LLMClient, LLMFile, LLMInput
from app.ai.prompts.cv_review import system_prompt, user_prompt
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.cv_review.schemas import CVComparisonResponse, CVReviewResponse


class CVReviewService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def review(
        self, *, files: list[LLMFile]
    ) -> CVReviewResponse | CVComparisonResponse:
        compare_mode = len(files) == 2

        resp = await self.llm.generate(
            inp=LLMInput(
                system=system_prompt("v1"),
                user=user_prompt(compare=compare_mode),
                files=files,
            )
        )

        schema = CVComparisonResponse if compare_mode else CVReviewResponse
        return parse_model_output(text=resp.text, schema=schema)