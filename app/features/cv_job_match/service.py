from app.ai.base import LLMClient, LLMFile, LLMInput
from app.ai.prompts.cv_job_match import system_prompt, user_prompt
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.cv_job_match.schemas import CVJobMatchResponse


class CVJobMatchService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def match(
        self,
        *,
        job_description: str,
        files: list[LLMFile] | None = None,
    ) -> CVJobMatchResponse:
        resp = await self.llm.generate(
            inp=LLMInput(
                system=system_prompt("v1"),
                user=user_prompt(job_description=job_description),
                files=files,
            )
        )

        return parse_model_output(text=resp.text, schema=CVJobMatchResponse)