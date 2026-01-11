from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class CVJobMatchRequest(BaseModel):
    cv_url: HttpUrl = Field(..., description="URL на PDF файл CV")
    job_description: str = Field(..., min_length=1, description="Описание вакансии")


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

    section_feedback: dict[str, str]