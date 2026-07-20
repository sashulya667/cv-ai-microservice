from pydantic import BaseModel, Field, field_validator

from app.features.shared.schemas import Resume, Vacancy

_RADAR_AXIS_FIELDS = ("skills", "experience", "domain", "location", "languages")


def _clamp_score(value: object) -> object:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    return min(100, max(0, round(value)))


class SearchCriterion(BaseModel):
    label: str
    value: str
    is_required: bool


class CandidatePayload(BaseModel):
    candidate_id: int
    resume: Resume


class CandidateRankRequest(BaseModel):
    vacancy: Vacancy
    required_criteria: list[SearchCriterion]
    desired_criteria: list[SearchCriterion]
    candidates: list[CandidatePayload] = Field(min_length=1, max_length=200)


class CriterionResult(BaseModel):
    label: str
    score: int = Field(ge=0, le=100)
    explanation: str


class RadarAxes(BaseModel):
    skills: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    domain: int = Field(ge=0, le=100)
    location: int = Field(ge=0, le=100)
    languages: int = Field(ge=0, le=100)

    @field_validator(*_RADAR_AXIS_FIELDS, mode="before")
    @classmethod
    def clamp_axes(cls, value: object) -> object:
        return _clamp_score(value)

    def mean_score(self) -> int:
        """Нейтральный baseline: равновзвешенное среднее по 5 осям."""
        return round(
            (self.skills + self.experience + self.languages + self.location + self.domain)
            / 5
        )


class RadarExplanations(BaseModel):
    skills: str
    experience: str
    domain: str
    location: str
    languages: str


class RankedCandidate(BaseModel):
    candidate_id: int
    total_score: int = Field(ge=0, le=100)
    criteria_results: list[CriterionResult]
    radar: RadarAxes
    radar_explanations: RadarExplanations
    strengths: list[str]
    risks: list[str]
    summary: str
    interview_questions: list[str]


class CandidateRankResponse(BaseModel):
    ranked_candidates: list[RankedCandidate]
