from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.features.shared.schemas import Education, WorkExperience

ResumeImportWarning = Literal[
    "incomplete_dates",
    "incomplete_education_years",
    "swapped_experience_dates",
    "swapped_education_years",
    "truncated_source",
    "low_confidence_city",
    "ambiguous_current_role",
    "low_confidence_extraction",
]

RESUME_IMPORT_WARNINGS: frozenset[str] = frozenset(
    {
        "incomplete_dates",
        "incomplete_education_years",
        "swapped_experience_dates",
        "swapped_education_years",
        "truncated_source",
        "low_confidence_city",
        "ambiguous_current_role",
        "low_confidence_extraction",
    }
)


class ResumeImportRequest(BaseModel):
    fileUrl: HttpUrl
    fileKey: str = Field(min_length=1)


class ResumeImportResponse(BaseModel):
    desiredPosition: Optional[str] = None
    about: Optional[str] = None
    city: Optional[str] = None
    skills: list[str] = []
    workExperiences: list[WorkExperience] = []
    education: list[Education] = []
    warnings: list[ResumeImportWarning] = []
