from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.features.shared.schemas import Resume, Vacancy

VALID_MODES = frozenset({"generate", "refine"})
VALID_TONES = frozenset({"neutral", "confident", "concise"})

DEFAULT_MAX_CHARS = 1500
MIN_MAX_CHARS = 300
MAX_MAX_CHARS = 2000


class CoverLetterOptions(BaseModel):
    tone: str = "neutral"
    maxChars: int = Field(default=DEFAULT_MAX_CHARS, ge=MIN_MAX_CHARS, le=MAX_MAX_CHARS)
    variants: int = Field(default=1, ge=1, le=2)

    @model_validator(mode="after")
    def normalize_tone(self) -> "CoverLetterOptions":
        if self.tone not in VALID_TONES:
            self.tone = "neutral"
        return self


class CoverLetterRequest(BaseModel):
    mode: str
    locale: str = "ru"
    resume: Resume
    vacancy: Optional[Vacancy] = None
    brief: Optional[str] = None
    currentText: Optional[str] = None
    refineInstruction: Optional[str] = None
    options: Optional[CoverLetterOptions] = None

    @model_validator(mode="after")
    def apply_defaults(self) -> "CoverLetterRequest":
        self.options = self.options or CoverLetterOptions()
        if self.brief is not None:
            stripped = self.brief.strip()
            self.brief = stripped or None
        if self.currentText is not None:
            stripped = self.currentText.strip()
            self.currentText = stripped or None
        if self.refineInstruction is not None:
            stripped = self.refineInstruction.strip()
            self.refineInstruction = stripped or None
        return self


class CoverLetterVariant(BaseModel):
    text: str
    rationale: str


class CoverLetterMeta(BaseModel):
    charCounts: list[int]
    usedVacancy: bool
    usedBrief: bool
    tone: str
    maxChars: int


class CoverLetterResponse(BaseModel):
    mode: str
    locale: str
    variants: list[CoverLetterVariant] = Field(min_length=1, max_length=2)
    warnings: list[str] = []
    meta: CoverLetterMeta
