import json
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.cv_job_match import system_prompt, user_prompt
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.cv_job_match.schemas import (
    ContextAnalysis,
    CVJobMatchResponse,
    Gap,
    ImpactAnalysis,
    LogisticsMatch,
)
from app.features.shared.schemas import Resume, Vacancy


class _LLMJobMatchResponse(BaseModel):
    """Внутренняя схема для парсинга LLM-ответа (без logistics_match — он считается отдельно)."""

    match_score: int = Field(ge=0, le=100)
    ats_match_score: int = Field(ge=0, le=100)
    seniority_fit: Literal["underqualified", "aligned", "overqualified"]
    overall_fit: Literal["poor", "moderate", "good", "strong"]
    summary: str
    matching_strengths: list[str]
    gaps: list[Gap]
    recommendations: list[str]
    matching_keywords: list[str]
    missing_keywords: list[str]
    impact_analysis: ImpactAnalysis
    context_analysis: ContextAnalysis
    section_feedback: dict[str, str]


def _resume_to_json(resume: Resume) -> str:
    return json.dumps(resume.model_dump(exclude_none=True), ensure_ascii=False, indent=2)


def _vacancy_to_json(vacancy: Vacancy) -> str:
    return json.dumps(vacancy.model_dump(exclude_none=True), ensure_ascii=False, indent=2)


def _compute_salary_match(
    resume: Resume, vacancy: Vacancy
) -> tuple[Literal["below", "aligned", "above", "unknown"], Optional[int]]:
    r_from = resume.desiredSalaryFrom
    r_to = resume.desiredSalaryTo
    v_from = vacancy.salaryFrom
    v_to = vacancy.salaryTo

    if not r_from and not r_to:
        return "unknown", None
    if not v_from and not v_to:
        return "unknown", None

    r_currency = (resume.salaryCurrency or "").upper()
    v_currency = (vacancy.salaryCurrency or "").upper()
    if r_currency and v_currency and r_currency != v_currency:
        return "unknown", None

    r_lo = r_from or r_to
    r_hi = r_to or r_from
    v_lo = v_from or v_to
    v_hi = v_to or v_from

    if r_lo <= v_hi and v_lo <= r_hi:  # type: ignore[operator]
        return "aligned", None

    r_mid = (r_lo + r_hi) / 2  # type: ignore[operator]
    v_mid = (v_lo + v_hi) / 2  # type: ignore[operator]
    gap_percent = round(abs(r_mid - v_mid) / v_mid * 100) if v_mid else None

    if r_mid > v_hi:  # type: ignore[operator]
        return "above", gap_percent
    return "below", gap_percent


def _compute_logistics_match(resume: Resume, vacancy: Vacancy) -> LogisticsMatch:
    salary_match, salary_gap_percent = _compute_salary_match(resume, vacancy)

    location_match = bool(
        resume.city
        and vacancy.city
        and resume.city.strip().lower() == vacancy.city.strip().lower()
    )

    work_format_match = False
    if resume.workFormats and vacancy.workFormat:
        v_fmt = vacancy.workFormat.lower()
        work_format_match = any(v_fmt in fmt.lower() or fmt.lower() in v_fmt for fmt in resume.workFormats)

    employment_type_match = False
    if resume.employmentTypes and vacancy.employmentType:
        v_emp = vacancy.employmentType.lower()
        employment_type_match = any(
            v_emp in emp.lower() or emp.lower() in v_emp for emp in resume.employmentTypes
        )

    return LogisticsMatch(
        salary_match=salary_match,
        salary_gap_percent=salary_gap_percent,
        location_match=location_match,
        work_format_match=work_format_match,
        employment_type_match=employment_type_match,
    )


class CVJobMatchService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def match(self, *, resume: Resume, vacancy: Vacancy) -> CVJobMatchResponse:
        resp = await self.llm.generate(
            inp=LLMInput(
                system=system_prompt("v1"),
                user=user_prompt(
                    resume_json=_resume_to_json(resume),
                    vacancy_json=_vacancy_to_json(vacancy),
                ),
            )
        )

        llm_result = parse_model_output(text=resp.text, schema=_LLMJobMatchResponse)

        return CVJobMatchResponse(
            **llm_result.model_dump(),
            logistics_match=_compute_logistics_match(resume, vacancy),
        )
