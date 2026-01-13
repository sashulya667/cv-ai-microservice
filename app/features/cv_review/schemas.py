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


class CVComparisonResponse(BaseModel):
    """Схема для сравнения двух версий CV (когда загружено 2 файла)"""

    current_overall_score: int = Field(ge=0, le=100, description="Оценка текущей версии CV")
    current_ats_score: int = Field(ge=0, le=100, description="ATS оценка текущей версии")
    previous_overall_score: int = Field(
        ge=0, le=100, description="Оценка предыдущей версии CV"
    )
    previous_ats_score: int = Field(ge=0, le=100, description="ATS оценка предыдущей версии")

    delta_overall: int = Field(description="Изменение overall_score")
    delta_ats: int = Field(description="Изменение ats_score")

    comparison_summary: str = Field(description="Краткий вердикт по изменениям (3-5 предложений)")
    improvements_made: list[str] = Field(
        description="Что конкретно улучшилось (с примерами до/после)"
    )
    regressions: list[str] = Field(
        description="Что ухудшилось или потеряно (пусто если ничего)"
    )
    still_broken: list[str] = Field(
        description="Проблемы, которые были и остались не исправлены"
    )
    next_steps: list[str] = Field(
        description="Топ-5 приоритетных правок для следующей итерации"
    )