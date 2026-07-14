import asyncio

from pydantic import BaseModel, Field

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.candidate_rank import system_prompt, user_prompt
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.candidate_rank.schemas import (
    CandidatePayload,
    CandidateRankRequest,
    CandidateRankResponse,
    CriterionResult,
    RadarAxes,
    RadarExplanations,
    RankedCandidate,
)

_CONCURRENCY = 10


class _LLMCandidateResult(BaseModel):
    criteria_results: list[CriterionResult]
    radar: RadarAxes
    radar_explanations: RadarExplanations
    strengths: list[str] = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
    summary: str = Field(min_length=1)


class CandidateRankService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def rank(self, *, payload: CandidateRankRequest) -> CandidateRankResponse:
        """Ранжирует батч кандидатов относительно вакансии и критериев работодателя."""
        semaphore = asyncio.Semaphore(_CONCURRENCY)

        async def _rank_one(candidate: CandidatePayload) -> RankedCandidate:
            async with semaphore:
                resp = await self.llm.generate(
                    inp=LLMInput(
                        system=system_prompt("v1"),
                        user=user_prompt(
                            vacancy=payload.vacancy,
                            required_criteria=payload.required_criteria,
                            desired_criteria=payload.desired_criteria,
                            resume=candidate.resume,
                        ),
                    )
                )
            result = parse_model_output(text=resp.text, schema=_LLMCandidateResult)
            return RankedCandidate(
                candidate_id=candidate.candidate_id,
                total_score=result.radar.mean_score(),
                criteria_results=result.criteria_results,
                radar=result.radar,
                radar_explanations=result.radar_explanations,
                strengths=result.strengths,
                risks=result.risks,
                summary=result.summary,
            )

        results = await asyncio.gather(*[_rank_one(c) for c in payload.candidates])
        ranked = sorted(results, key=lambda r: r.total_score, reverse=True)
        return CandidateRankResponse(ranked_candidates=ranked)
