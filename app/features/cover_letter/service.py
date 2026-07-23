from pydantic import BaseModel, Field

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.cover_letter import resolve_locale, system_prompt, user_prompt
from app.common.errors import UpstreamError
from app.common.parsing import parse_model_output
from app.config import Settings
from app.features.cover_letter.schemas import (
    CoverLetterMeta,
    CoverLetterRequest,
    CoverLetterResponse,
    CoverLetterVariant,
)
from app.features.cover_letter.validator import used_brief, used_vacancy, validate_request


class _LLMVariant(BaseModel):
    text: str
    rationale: str


class _LLMCoverLetterResponse(BaseModel):
    variants: list[_LLMVariant] = Field(min_length=1, max_length=2)
    warnings: list[str] = []


def _truncate(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    cut = text[:max_chars].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    cut = cut.rstrip(".,;:!?-–—")
    return cut, True


def _merge_warnings(*groups: list[str]) -> list[str]:
    seen: list[str] = []
    for group in groups:
        for item in group:
            if item not in seen:
                seen.append(item)
    return seen


def _normalize_variant(
    *,
    variant: _LLMVariant,
    max_chars: int,
) -> tuple[CoverLetterVariant, list[str]]:
    warnings: list[str] = []
    text = (variant.text or "").strip()
    if not text:
        return (
            CoverLetterVariant(text="", rationale=(variant.rationale or "").strip()),
            warnings,
        )

    text, was_truncated = _truncate(text, max_chars)
    if was_truncated:
        warnings.append("truncated_to_max_chars")

    rationale = (variant.rationale or "").strip() or "Акцент на релевантном опыте кандидата."
    return CoverLetterVariant(text=text, rationale=rationale), warnings


class CoverLetterService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def generate(self, *, request: CoverLetterRequest) -> CoverLetterResponse:
        pre_warnings = validate_request(request)
        opts = request.options
        assert opts is not None

        locale, locale_fallback = resolve_locale(request.locale)
        if locale_fallback:
            pre_warnings = _merge_warnings(pre_warnings, ["locale_fallback"])

        resp = await self.llm.generate(
            inp=LLMInput(
                system=system_prompt("v1"),
                user=user_prompt(request=request, locale=locale),
            )
        )
        llm_result = parse_model_output(text=resp.text, schema=_LLMCoverLetterResponse)

        variants: list[CoverLetterVariant] = []
        post_warnings: list[str] = []
        wanted = opts.variants

        for raw in llm_result.variants[:wanted]:
            variant, w = _normalize_variant(variant=raw, max_chars=opts.maxChars)
            if not variant.text:
                continue
            variants.append(variant)
            post_warnings.extend(w)

        if not variants:
            raise UpstreamError("Model returned no cover letter variants")

        if wanted > 1 and len(variants) < wanted:
            post_warnings.append("single_variant_only")

        return CoverLetterResponse(
            mode=request.mode,
            locale=locale,
            variants=variants[:wanted],
            warnings=_merge_warnings(pre_warnings, llm_result.warnings, post_warnings),
            meta=CoverLetterMeta(
                charCounts=[len(v.text) for v in variants[:wanted]],
                usedVacancy=used_vacancy(request),
                usedBrief=used_brief(request),
                tone=opts.tone,
                maxChars=opts.maxChars,
            ),
        )
