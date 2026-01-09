from pydantic import BaseModel, Field


class CVReviewResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    ats_score: int = Field(ge=0, le=100)
    summary: str

    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]

    section_feedback: dict[str, str]
