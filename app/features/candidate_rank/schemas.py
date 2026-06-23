from pydantic import BaseModel, Field

from app.features.shared.schemas import Resume, Vacancy


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


class RankedCandidate(BaseModel):
    candidate_id: int
    total_score: int = Field(ge=0, le=100)
    criteria_results: list[CriterionResult]
    radar: RadarAxes
    summary: str


class CandidateRankResponse(BaseModel):
    ranked_candidates: list[RankedCandidate]
