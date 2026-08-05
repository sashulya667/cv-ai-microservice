from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.ai.base import LLMClient, LLMInput
from app.ai.prompts.resume_import import system_prompt, user_prompt
from app.common.errors import BadRequest, UnprocessableEntity
from app.common.http_client import download_file_from_url
from app.common.parsing import parse_model_output
from app.common.pdf import extract_text_from_pdf
from app.config import Settings
from app.features.resume_import.schemas import (
    RESUME_IMPORT_WARNINGS,
    ResumeImportRequest,
    ResumeImportResponse,
    ResumeImportWarning,
)
from app.features.shared.schemas import Education, WorkExperience

_SKILL_MAX_LEN = 100
_SKILLS_MAX_COUNT = 30
_DESCRIPTION_MAX_LEN = 8_000
_ABOUT_MAX_LEN = 4_000
_STRING_MAX_LEN = 300

_DATE_YMD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DATE_YM = re.compile(r"^(\d{4})-(\d{2})$")
_DATE_Y = re.compile(r"^(\d{4})$")
_DATE_DMY = re.compile(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$")
_DATE_MY = re.compile(r"^(\d{1,2})[./](\d{4})$")
_DATE_ISO_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")


class _LLMResumeImportResponse(BaseModel):
    desiredPosition: Optional[str] = None
    about: Optional[str] = None
    city: Optional[str] = None
    skills: list[str] = []
    workExperiences: list[WorkExperience] = []
    education: list[Education] = []
    warnings: list[str] = []


def _clean_str(value: Optional[str], *, max_len: int = _STRING_MAX_LEN) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(value.replace("\u00a0", " ").split()).strip(" -,;|")
    if not text:
        return None
    if len(text) > max_len:
        text = text[:max_len].rstrip(" -,;|")
    return text or None


def _clean_multiline(value: Optional[str], *, max_len: int) -> Optional[str]:
    if value is None:
        return None
    text = value.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text:
        return None
    if len(text) > max_len:
        text = text[:max_len].rstrip()
    return text or None


def _normalize_skill(value: str) -> Optional[str]:
    name = " ".join(value.replace("\n", " ").split()).strip(" -•*,;")
    if not name:
        return None
    if len(name) > _SKILL_MAX_LEN:
        name = name[:_SKILL_MAX_LEN].rstrip(" -•*,;")
    return name or None


def _normalize_skills(values: list[str] | None, *, limit: int = _SKILLS_MAX_COUNT) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        parts = re.split(r"\s*[;|]\s*", raw) if raw else []
        for part in parts or [raw]:
            name = _normalize_skill(part or "")
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(name)
            if len(result) >= limit:
                return result
    return result


def _clamp_int_year(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    year = int(value)
    if year < 1950 or year > date.today().year + 8:
        return None
    return year


def _valid_calendar_date(year: int, month: int, day: int) -> Optional[str]:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        try:
            return date(year, month, 1).isoformat()
        except ValueError:
            return None


def normalize_date(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None

    lower = raw.casefold()
    if lower in {"present", "current", "now", "сегодня", "настоящее время", "н.в.", "н.в", "по н.в."}:
        return None

    m = _DATE_YMD.match(raw)
    if m:
        return _valid_calendar_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    m = _DATE_YM.match(raw)
    if m:
        return _valid_calendar_date(int(m.group(1)), int(m.group(2)), 1)

    m = _DATE_Y.match(raw)
    if m:
        return _valid_calendar_date(int(m.group(1)), 1, 1)

    m = _DATE_DMY.match(raw)
    if m:
        return _valid_calendar_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    m = _DATE_MY.match(raw)
    if m:
        return _valid_calendar_date(int(m.group(2)), int(m.group(1)), 1)

    m = _DATE_ISO_PREFIX.match(raw)
    if m:
        return normalize_date(m.group(1))

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %Y", "%B %Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            day = dt.day if "%d" in fmt else 1
            return _valid_calendar_date(dt.year, dt.month, day)
        except ValueError:
            continue

    return None


def _merge_warnings(*groups: list[str]) -> list[ResumeImportWarning]:
    seen: list[ResumeImportWarning] = []
    for group in groups:
        for item in group:
            code = (item or "").strip()
            if code in RESUME_IMPORT_WARNINGS and code not in seen:
                seen.append(code)  # type: ignore[arg-type]
    return seen


def _normalize_work(item: WorkExperience) -> Optional[tuple[WorkExperience, list[str]]]:
    warnings: list[str] = []
    company = _clean_str(item.companyName)
    position = _clean_str(item.position)
    if not company or not position:
        return None

    start = normalize_date(item.startDate)
    end = normalize_date(item.endDate)
    is_current = bool(item.isCurrent)

    if item.startDate and not start:
        warnings.append("incomplete_dates")
    if item.endDate and not end and not is_current:
        warnings.append("incomplete_dates")

    if is_current:
        end = None

    if start and end and start > end:
        start, end = end, start
        warnings.append("swapped_experience_dates")

    return (
        WorkExperience(
            companyName=company,
            position=position,
            startDate=start,
            endDate=end,
            isCurrent=is_current,
            description=_clean_multiline(item.description, max_len=_DESCRIPTION_MAX_LEN),
            skills=_normalize_skills(item.skills),
        ),
        warnings,
    )


def _normalize_education(item: Education) -> Optional[tuple[Education, list[str]]]:
    warnings: list[str] = []
    institution = _clean_str(item.institutionName, max_len=400)
    if not institution:
        return None

    start_year = _clamp_int_year(item.startYear)
    end_year = _clamp_int_year(item.endYear)
    is_current = bool(item.isCurrent)

    if item.startYear is not None and start_year is None:
        warnings.append("incomplete_education_years")
    if item.endYear is not None and end_year is None:
        warnings.append("incomplete_education_years")

    if is_current:
        end_year = None

    if start_year and end_year and start_year > end_year:
        start_year, end_year = end_year, start_year
        warnings.append("swapped_education_years")

    return (
        Education(
            institutionName=institution,
            degree=_clean_str(item.degree),
            fieldOfStudy=_clean_str(item.fieldOfStudy),
            startYear=start_year,
            endYear=end_year,
            isCurrent=is_current,
            description=_clean_multiline(item.description, max_len=_DESCRIPTION_MAX_LEN),
        ),
        warnings,
    )


def _is_useful(result: ResumeImportResponse) -> bool:
    has_experience = any(
        exp.companyName and exp.position for exp in result.workExperiences
    )
    has_education = any(edu.institutionName for edu in result.education)
    has_skills_and_position = bool(result.skills) and bool(result.desiredPosition)
    return has_experience or has_education or has_skills_and_position


def _normalize_result(
    raw: _LLMResumeImportResponse,
    *,
    extra_warnings: list[str],
) -> ResumeImportResponse:
    post_warnings: list[str] = []
    experiences: list[WorkExperience] = []
    education: list[Education] = []

    for item in raw.workExperiences:
        normalized = _normalize_work(item)
        if normalized is None:
            continue
        exp, w = normalized
        experiences.append(exp)
        post_warnings.extend(w)

    for item in raw.education:
        normalized = _normalize_education(item)
        if normalized is None:
            continue
        edu, w = normalized
        education.append(edu)
        post_warnings.extend(w)

    return ResumeImportResponse(
        desiredPosition=_clean_str(raw.desiredPosition),
        about=_clean_multiline(raw.about, max_len=_ABOUT_MAX_LEN),
        city=_clean_str(raw.city),
        skills=_normalize_skills(raw.skills),
        workExperiences=experiences,
        education=education,
        warnings=_merge_warnings(extra_warnings, raw.warnings, post_warnings),
    )


class ResumeImportService:
    def __init__(self, *, settings: Settings, llm: LLMClient) -> None:
        self.settings = settings
        self.llm = llm

    async def parse(self, *, request: ResumeImportRequest) -> ResumeImportResponse:
        file_key = request.fileKey.strip()
        if not file_key:
            raise BadRequest("fileKey пустой")

        pdf_bytes = await download_file_from_url(
            str(request.fileUrl),
            timeout=self.settings.pdf_download_timeout,
            max_size_mb=self.settings.pdf_max_size_mb,
            max_retries=self.settings.pdf_download_retries,
        )

        text = extract_text_from_pdf(
            pdf_bytes,
            max_pages=self.settings.pdf_max_pages,
        )

        extra_warnings: list[str] = []
        max_chars = self.settings.resume_text_max_chars
        if len(text) > max_chars:
            text = text[:max_chars].rstrip()
            extra_warnings.append("truncated_source")

        resp = await self.llm.generate(
            inp=LLMInput(
                system=system_prompt("v1"),
                user=user_prompt(resume_text=text),
            )
        )
        llm_result = parse_model_output(text=resp.text, schema=_LLMResumeImportResponse)
        result = _normalize_result(llm_result, extra_warnings=extra_warnings)

        if not _is_useful(result):
            raise UnprocessableEntity(
                error="unprocessable_resume",
                detail="Не удалось извлечь полезные поля из резюме",
            )

        return result
