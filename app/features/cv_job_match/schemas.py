from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.features.shared.schemas import Resume, Vacancy


class CVJobMatchRequest(BaseModel):
    resume: Resume
    vacancy: Vacancy


class Gap(BaseModel):
    type: Literal["must_have_skill", "must_have_context", "seniority_gap", "nice_to_have"] = Field(
        description="Тип пробела: must_have_skill — критичный навык, must_have_context — нет опыта в релевантной среде, seniority_gap — уровень задач ниже требуемого, nice_to_have — желательное, не критичное"
    )
    text: str = Field(description="Описание пробела")


class LogisticsMatch(BaseModel):
    salary_match: Literal["below", "aligned", "above", "unknown"] = Field(
        description="Сравнение желаемой зарплаты кандидата с вилкой вакансии"
    )
    salary_gap_percent: Optional[int] = Field(
        default=None,
        description="Расхождение в % если не aligned (None если unknown или aligned)"
    )
    location_match: bool = Field(description="Совпадение города кандидата и вакансии")
    work_format_match: bool = Field(
        description="Совпадение формата работы (remote/hybrid/office)"
    )
    employment_type_match: bool = Field(
        description="Совпадение типа занятости (full_time/part_time/...)"
    )


class ImpactAnalysis(BaseModel):
    achievements_quality: Literal["weak", "moderate", "strong"] = Field(
        description="Общая оценка качества достижений"
    )
    measurability_score: int = Field(
        ge=0, le=100, description="Процент достижений с конкретными метриками"
    )
    xyz_formula_usage: int = Field(
        ge=0,
        le=100,
        description="Процент достижений по формуле X-Y-Z (Достиг X, измерил в Y, через Z)",
    )
    leadership_evidence: list[str] = Field(description="Конкретные примеры лидерства из CV")
    individual_impact: list[str] = Field(description="Личные достижения с четкими метриками")
    red_flags: list[str] = Field(description="Тревожные сигналы в достижениях")


class ContextAnalysis(BaseModel):
    company_scale_match: Literal["mismatch", "partial", "aligned"] = Field(
        description="Соответствие масштаба компаний в опыте требованиям вакансии"
    )
    task_scale_match: Literal["mismatch", "partial", "aligned"] = Field(
        description="Соответствие масштаба задач требованиям вакансии"
    )
    autonomy_level: Literal["executor", "designer", "decision_maker", "owner"] = Field(
        description="Уровень самостоятельности кандидата"
    )
    complexity_match: str = Field(description="Анализ соответствия сложности задач (3-5 предложений)")
    environment_fit: str = Field(description="Соответствие среды опыта среде вакансии (2-3 предложения)")


class CVJobMatchResponse(BaseModel):
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

    logistics_match: LogisticsMatch
    impact_analysis: ImpactAnalysis
    context_analysis: ContextAnalysis

    section_feedback: dict[str, str]
