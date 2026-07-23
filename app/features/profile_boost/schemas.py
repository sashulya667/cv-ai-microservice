from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.features.shared.schemas import Resume

VALID_TARGETS = frozenset({"about", "experience", "skills"})
VALID_MODES = frozenset({"improve", "generate"})
VALID_TONES = frozenset({"neutral", "confident", "concise"})

DEFAULT_MAX_CHARS: dict[str, int] = {
    "about": 600,
    "experience": 1200,
}


class FocusExperience(BaseModel):
    companyName: Optional[str] = None
    position: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isCurrent: bool = False
    description: Optional[str] = None
    skills: list[str] = []


class ProfileBoostFocus(BaseModel):
    currentText: Optional[str] = None
    experienceIndex: Optional[int] = None
    experience: Optional[FocusExperience] = None


class ProfileBoostOptions(BaseModel):
    tone: str = "neutral"
    variants: int = Field(default=1, ge=1, le=2)
    maxChars: Optional[int] = Field(default=None, ge=50, le=5000)

    @model_validator(mode="after")
    def normalize_tone(self) -> "ProfileBoostOptions":
        if self.tone not in VALID_TONES:
            self.tone = "neutral"
        return self


class ProfileBoostRequest(BaseModel):
    target: str
    mode: str
    locale: str = "ru"
    resume: Resume
    focus: Optional[ProfileBoostFocus] = None
    options: Optional[ProfileBoostOptions] = None

    @model_validator(mode="after")
    def apply_defaults(self) -> "ProfileBoostRequest":
        opts = self.options or ProfileBoostOptions()
        if opts.maxChars is None and self.target in DEFAULT_MAX_CHARS:
            opts = opts.model_copy(update={"maxChars": DEFAULT_MAX_CHARS[self.target]})
        self.options = opts
        if self.focus is None:
            self.focus = ProfileBoostFocus()
        return self


class ProfileBoostVariant(BaseModel):
    text: Optional[str] = None
    skills: Optional[list[str]] = None
    addedSkills: Optional[list[str]] = None
    removedSkills: Optional[list[str]] = None
    rationale: str


class ProfileBoostResponse(BaseModel):
    target: str
    mode: str
    variants: list[ProfileBoostVariant] = Field(min_length=1, max_length=2)
    warnings: list[str] = []
