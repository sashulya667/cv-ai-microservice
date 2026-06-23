from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.features.shared.schemas import Resume


class CVReviewRequest(BaseModel):
    resume: Optional[Resume] = None
    currentResume: Optional[Resume] = None
    previousResume: Optional[Resume] = None

    @model_validator(mode="after")
    def _validate_mode(self) -> "CVReviewRequest":
        has_single = self.resume is not None
        has_both = self.currentResume is not None and self.previousResume is not None
        has_partial = (self.currentResume is None) != (self.previousResume is None)

        if has_partial:
            raise ValueError(
                "Для сравнения необходимо передать оба поля: 'currentResume' и 'previousResume'."
            )
        if not has_single and not has_both:
            raise ValueError(
                "Укажите 'resume' для анализа или 'currentResume' + 'previousResume' для сравнения."
            )
        if has_single and has_both:
            raise ValueError(
                "Нельзя передавать 'resume' вместе с 'currentResume'/'previousResume'."
            )
        return self

    @property
    def is_comparison(self) -> bool:
        return self.currentResume is not None


class CVReviewResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    ats_score: int = Field(ge=0, le=100)
    summary: str

    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]

    experience_gaps: list[str] = Field(
        description="Пробелы в карьере: даты и продолжительность (пустой список если нет)"
    )
    section_feedback: dict[str, str]


class CVComparisonResponse(BaseModel):
    current_overall_score: int = Field(ge=0, le=100, description="Оценка текущей версии CV")
    current_ats_score: int = Field(ge=0, le=100, description="ATS оценка текущей версии")
    previous_overall_score: int = Field(ge=0, le=100, description="Оценка предыдущей версии CV")
    previous_ats_score: int = Field(ge=0, le=100, description="ATS оценка предыдущей версии")

    delta_overall: int = Field(description="Изменение overall_score")
    delta_ats: int = Field(description="Изменение ats_score")

    comparison_summary: str = Field(description="Краткий вердикт по изменениям (3-5 предложений)")
    improvements_made: list[str] = Field(
        description="Что конкретно улучшилось (с примерами до/после)"
    )
    regressions: list[str] = Field(description="Что ухудшилось или потеряно (пустой список если нет)")
    still_broken: list[str] = Field(description="Проблемы из старой версии, которые не исправлены")
    next_steps: list[str] = Field(description="Топ-5 приоритетных правок для следующей итерации")
