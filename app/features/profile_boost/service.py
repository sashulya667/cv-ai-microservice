import re
from typing import Optional

from pydantic import BaseModel, Field

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.profile_boost import system_prompt, user_prompt
from app.common.errors import UpstreamError
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.profile_boost.schemas import (
    ProfileBoostRequest,
    ProfileBoostResponse,
    ProfileBoostVariant,
)
from app.features.profile_boost.validator import validate_request

_SKILL_MAX_LEN = 100
_SKILLS_MAX_COUNT = 30


class _LLMVariant(BaseModel):
    text: Optional[str] = None
    skills: Optional[list[str]] = None
    addedSkills: Optional[list[str]] = None
    removedSkills: Optional[list[str]] = None
    rationale: str


class _LLMProfileBoostResponse(BaseModel):
    variants: list[_LLMVariant] = Field(min_length=1, max_length=2)
    warnings: list[str] = []


def _truncate(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    cut = text[: max_chars - 1].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…", True


def _normalize_skill_name(value: str) -> str | None:
    name = " ".join(value.replace("\n", " ").split()).strip(" -•*,;")
    if not name:
        return None
    if len(name) > _SKILL_MAX_LEN:
        name = name[:_SKILL_MAX_LEN].rstrip(" -•*,;")
    return name or None


def _normalize_skills(values: list[str] | None, *, limit: int | None = None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        for part in re.split(r"\s*[;|]\s*", raw) if raw else []:
            name = _normalize_skill_name(part)
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(name)
            if limit is not None and len(result) >= limit:
                return result
    return result


def _normalize_variant(
    *,
    variant: _LLMVariant,
    target: str,
    max_chars: int | None,
) -> tuple[ProfileBoostVariant, list[str]]:
    warnings: list[str] = []
    text = variant.text
    skills = variant.skills
    added = variant.addedSkills
    removed = variant.removedSkills

    if target == "about":
        skills = None
        added = None
        removed = None
        if text is None:
            text = ""
        if max_chars is not None and text:
            text, was_truncated = _truncate(text, max_chars)
            if was_truncated:
                warnings.append("truncated_output")
    elif target == "experience":
        skills = _normalize_skills(skills, limit=_SKILLS_MAX_COUNT)
        added = _normalize_skills(added)
        removed = _normalize_skills(removed)
        if text is None:
            text = ""
        if max_chars is not None and text:
            text, was_truncated = _truncate(text, max_chars)
            if was_truncated:
                warnings.append("truncated_output")
    else:
        text = None
        skills = _normalize_skills(skills, limit=_SKILLS_MAX_COUNT)
        added = _normalize_skills(added)
        removed = _normalize_skills(removed)

    return (
        ProfileBoostVariant(
            text=text,
            skills=skills,
            addedSkills=added,
            removedSkills=removed,
            rationale=variant.rationale.strip() or "Черновик на основе данных профиля",
        ),
        warnings,
    )


def _merge_warnings(*groups: list[str]) -> list[str]:
    seen: list[str] = []
    for group in groups:
        for item in group:
            if item not in seen:
                seen.append(item)
    return seen


class ProfileBoostService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def boost(self, *, request: ProfileBoostRequest) -> ProfileBoostResponse:
        pre_warnings = validate_request(request)
        opts = request.options
        assert opts is not None

        resp = await self.llm.generate(
            inp=LLMInput(
                system=system_prompt("v1"),
                user=user_prompt(request=request),
            )
        )
        llm_result = parse_model_output(text=resp.text, schema=_LLMProfileBoostResponse)

        variants: list[ProfileBoostVariant] = []
        post_warnings: list[str] = []
        wanted = opts.variants

        for raw in llm_result.variants[:wanted]:
            variant, w = _normalize_variant(
                variant=raw,
                target=request.target,
                max_chars=opts.maxChars,
            )
            variants.append(variant)
            post_warnings.extend(w)

        if not variants:
            raise UpstreamError("Model returned no variants")

        return ProfileBoostResponse(
            target=request.target,
            mode=request.mode,
            variants=variants[:wanted],
            warnings=_merge_warnings(pre_warnings, llm_result.warnings, post_warnings),
        )
