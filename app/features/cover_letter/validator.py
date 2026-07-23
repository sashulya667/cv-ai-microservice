from app.common.errors import UnprocessableEntity
from app.features.cover_letter.schemas import VALID_MODES, CoverLetterRequest
from app.features.shared.schemas import Resume, Vacancy


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _vacancy_has_content(vacancy: Vacancy | None) -> bool:
    if vacancy is None:
        return False
    return bool(
        _strip_or_none(vacancy.title)
        or _strip_or_none(vacancy.description)
        or vacancy.skills
        or _strip_or_none(vacancy.specialization)
    )


def _resume_has_generate_content(resume: Resume) -> bool:
    return bool(
        resume.workExperiences
        or _strip_or_none(resume.about)
        or resume.skills
        or _strip_or_none(resume.desiredPosition)
        or _strip_or_none(resume.title)
        or resume.specializations
        or resume.education
    )


def validate_request(request: CoverLetterRequest) -> list[str]:
    if request.mode not in VALID_MODES:
        raise UnprocessableEntity(
            error="invalid_mode",
            detail=f"Unknown mode: {request.mode}",
        )

    if request.mode == "refine" and not request.currentText:
        raise UnprocessableEntity(
            error="empty_current_text",
            detail="currentText is required and must be non-empty when mode=refine",
        )

    warnings: list[str] = []

    if request.mode == "generate":
        if not _resume_has_generate_content(request.resume):
            warnings.append("insufficient_resume_content")
        if not _vacancy_has_content(request.vacancy) and not request.brief:
            warnings.append("no_vacancy_or_brief")

    return warnings


def used_vacancy(request: CoverLetterRequest) -> bool:
    return _vacancy_has_content(request.vacancy)


def used_brief(request: CoverLetterRequest) -> bool:
    return bool(request.brief)
