from pydantic import BaseModel, Field, HttpUrl


class CVReviewRequest(BaseModel):
    cv_urls: list[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=2,
        description="Список URL на PDF файлы CV (1-2 файла)",
    )


class CVReviewResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    ats_score: int = Field(ge=0, le=100)
    summary: str

    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]

    section_feedback: dict[str, str]
