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
    RankedCandidate,
)

_CONCURRENCY = 10


class _LLMCandidateResult(BaseModel):
    criteria_results: list[CriterionResult]
    radar: RadarAxes
    summary: str = Field(min_length=1)


def _compute_total_score(radar: RadarAxes) -> int:
    """Взвешенный итоговый скор: Skills 40%, Experience 30%, Domain 20%, Location 10%."""
    raw = (
        radar.skills * 0.40
        + radar.experience * 0.30
        + radar.domain * 0.20
        + radar.location * 0.10
    )
    return min(100, max(0, round(raw)))


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
                total_score=_compute_total_score(result.radar),
                criteria_results=result.criteria_results,
                radar=result.radar,
                summary=result.summary,
            )

        results = await asyncio.gather(*[_rank_one(c) for c in payload.candidates])
        ranked = sorted(results, key=lambda r: r.total_score, reverse=True)
        return CandidateRankResponse(ranked_candidates=ranked)
