from app.common.errors import UnprocessableEntity
from app.features.profile_boost.schemas import (
    VALID_MODES,
    VALID_TARGETS,
    FocusExperience,
    ProfileBoostRequest,
)
from app.features.shared.schemas import Resume


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _has_experience_anchor(exp: FocusExperience) -> bool:
    if not _strip_or_none(exp.position):
        return False
    return bool(
        _strip_or_none(exp.companyName)
        or _strip_or_none(exp.startDate)
        or _strip_or_none(exp.endDate)
        or exp.isCurrent
    )


def _about_source(request: ProfileBoostRequest) -> str | None:
    focus = request.focus
    if focus:
        current = _strip_or_none(focus.currentText)
        if current:
            return current
    return _strip_or_none(request.resume.about)


def _resume_has_generate_context(resume: Resume) -> bool:
    return bool(
        _strip_or_none(resume.desiredPosition)
        or resume.workExperiences
        or _strip_or_none(resume.about)
        or resume.specializations
    )


def _is_sparse(request: ProfileBoostRequest) -> bool:
    resume = request.resume
    if request.target == "about":
        facts = sum(
            [
                1 if _strip_or_none(resume.desiredPosition) else 0,
                min(len(resume.workExperiences), 2),
                1 if len(resume.skills) >= 3 else 0,
                1 if _strip_or_none(resume.about) else 0,
                1 if resume.experienceYears else 0,
                1 if resume.education else 0,
                1 if resume.languages else 0,
                1 if resume.certificates else 0,
                1 if resume.portfolio else 0,
                1 if resume.specializations else 0,
            ]
        )
        return facts < 2
    if request.target == "experience":
        exp = request.focus.experience if request.focus else None
        if not exp:
            return True
        return not (
            _strip_or_none(exp.description) or exp.skills or len(resume.skills) >= 2
        )
    return (
        len(resume.skills) < 2
        and not resume.workExperiences
        and not _strip_or_none(resume.about)
    )


def validate_request(request: ProfileBoostRequest) -> list[str]:
    if request.target not in VALID_TARGETS:
        raise UnprocessableEntity(
            error="invalid_target",
            detail=f"Unknown target: {request.target}",
        )
    if request.mode not in VALID_MODES:
        raise UnprocessableEntity(
            error="invalid_mode",
            detail=f"Unknown mode: {request.mode}",
        )

    target = request.target
    mode = request.mode
    resume = request.resume
    focus = request.focus

    if target == "about":
        if mode == "improve" and not _about_source(request):
            raise UnprocessableEntity(
                error="empty_current_text",
                detail="Need non-empty about or focus.currentText to improve",
            )
        if mode == "generate":
            has_position = bool(_strip_or_none(resume.desiredPosition))
            has_experience = len(resume.workExperiences) >= 1
            has_skills = len(resume.skills) >= 3
            if not (has_position or has_experience or has_skills):
                raise UnprocessableEntity(
                    error="insufficient_profile_data",
                    detail=(
                        "Need desiredPosition, work experience, or at least 3 skills "
                        "to generate about"
                    ),
                )

    elif target == "experience":
        if not focus or not focus.experience:
            raise UnprocessableEntity(
                error="missing_focus_experience",
                detail="focus.experience is required when target=experience",
            )
        exp = focus.experience
        if not _has_experience_anchor(exp):
            raise UnprocessableEntity(
                error="insufficient_profile_data",
                detail=(
                    "focus.experience needs position and companyName or dates "
                    "to generate/improve experience"
                ),
            )
        if mode == "improve" and not _strip_or_none(exp.description):
            raise UnprocessableEntity(
                error="empty_current_text",
                detail="Need non-empty focus.experience.description to improve",
            )

    elif target == "skills":
        if mode == "improve" and not resume.skills:
            raise UnprocessableEntity(
                error="empty_current_text",
                detail="Need non-empty resume.skills to improve",
            )
        if mode == "generate" and not _resume_has_generate_context(resume):
            raise UnprocessableEntity(
                error="insufficient_profile_data",
                detail=(
                    "Need work experience, about, or desiredPosition "
                    "to generate skills"
                ),
            )

    warnings: list[str] = []
    if _is_sparse(request):
        warnings.append("insufficient_detail")
    return warnings
