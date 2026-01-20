from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class CVJobMatchRequest(BaseModel):
    cv_url: HttpUrl = Field(..., description="URL на PDF файл CV")
    job_description: str = Field(..., min_length=1, description="Описание вакансии")


class ImpactAnalysis(BaseModel):
    """Анализ качества достижений и измеримости результатов в CV"""

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
    leadership_evidence: list[str] = Field(
        description="Конкретные примеры лидерства из CV"
    )
    individual_impact: list[str] = Field(
        description="Личные достижения с четкими метриками"
    )
    red_flags: list[str] = Field(description="Тревожные сигналы в достижениях")


class ContextAnalysis(BaseModel):
    """Анализ масштаба и релевантности опыта"""

    company_scale_match: Literal["mismatch", "partial", "aligned"] = Field(
        description="Соответствие масштаба компаний в опыте требованиям вакансии"
    )
    task_scale_match: Literal["mismatch", "partial", "aligned"] = Field(
        description="Соответствие масштаба задач требованиям вакансии"
    )
    autonomy_level: Literal["executor", "designer", "decision_maker", "owner"] = Field(
        description="Уровень самостоятельности кандидата"
    )
    complexity_match: str = Field(
        description="Анализ соответствия сложности задач (3-5 предложений)"
    )
    environment_fit: str = Field(
        description="Соответствие среды опыта среде вакансии (2-3 предложения)"
    )


class CVJobMatchResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    ats_match_score: int = Field(ge=0, le=100)

    seniority_fit: Literal["underqualified", "aligned", "overqualified"]
    overall_fit: Literal["poor", "moderate", "good", "strong"]

    summary: str

    matching_strengths: list[str]
    gaps: list[str]
    recommendations: list[str]

    matching_keywords: list[str]
    missing_keywords: list[str]

    impact_analysis: ImpactAnalysis
    context_analysis: ContextAnalysis

    section_feedback: dict[str, str]