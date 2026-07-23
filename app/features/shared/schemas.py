import html
import re
from typing import Optional

from pydantic import BaseModel, field_validator


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())


class WorkExperience(BaseModel):
    companyName: str
    position: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isCurrent: bool = False
    description: Optional[str] = None
    skills: list[str] = []


class Education(BaseModel):
    institutionName: str
    degree: Optional[str] = None
    fieldOfStudy: Optional[str] = None
    startYear: Optional[int] = None
    endYear: Optional[int] = None
    isCurrent: bool = False
    description: Optional[str] = None


class Language(BaseModel):
    name: str
    code: str
    level: Optional[str] = None


class Certificate(BaseModel):
    name: str
    issuingOrganization: Optional[str] = None
    issueYear: Optional[int] = None
    issueMonth: Optional[int] = None
    expiryYear: Optional[int] = None
    expiryMonth: Optional[int] = None
    doesNotExpire: bool = False


class Portfolio(BaseModel):
    type: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    year: Optional[int] = None


class Recommendation(BaseModel):
    authorName: str
    position: Optional[str] = None
    company: Optional[str] = None
    rating: Optional[int] = None
    text: Optional[str] = None


class Resume(BaseModel):
    title: Optional[str] = None
    desiredPosition: Optional[str] = None
    about: Optional[str] = None
    experienceYears: Optional[int] = None
    city: Optional[str] = None
    desiredSalaryFrom: Optional[int] = None
    desiredSalaryTo: Optional[int] = None
    salaryCurrency: Optional[str] = None
    workFormats: list[str] = []
    employmentTypes: list[str] = []
    specializations: list[str] = []
    skills: list[str] = []
    workExperiences: list[WorkExperience] = []
    education: list[Education] = []
    languages: list[Language] = []
    certificates: list[Certificate] = []
    portfolio: list[Portfolio] = []
    recommendations: list[Recommendation] = []


class Vacancy(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v: object) -> object:
        if isinstance(v, str):
            return _strip_html(v)
        return v
    specialization: Optional[str] = None
    experienceRequired: Optional[str] = None
    city: Optional[str] = None
    employmentType: Optional[str] = None
    workFormat: Optional[str] = None
    workSchedule: Optional[str] = None
    workHoursPerDay: Optional[str] = None
    salaryFrom: Optional[int] = None
    salaryTo: Optional[int] = None
    salaryCurrency: Optional[str] = None
    salaryPeriod: Optional[str] = None
    salaryType: Optional[str] = None
    isInternship: bool = False
    isPartTimeJob: bool = False
    skills: list[str] = []
