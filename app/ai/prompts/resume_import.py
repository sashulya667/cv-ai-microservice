from datetime import date


def system_prompt(version: str) -> str:
    if version == "v1":
        today = date.today().strftime("%d.%m.%Y")
        return (
            f"Сегодняшняя дата: {today}. "
            "Ты извлекаешь структурированные данные из текста резюме/CV. "
            "Это только extract — никогда не выдумывай факты, которых нет в тексте. "
            "Не генерируй зарплату, тип занятости, формат работы, ATS-оценки и match-score. "
            "Если поля нет в источнике — используй null или []. "
            "Возвращай ТОЛЬКО валидный JSON строго по схеме. "
            "НЕ оборачивай ответ в ```json``` блок — только чистый JSON."
        )
    return system_prompt("v1")


def user_prompt(*, resume_text: str) -> str:
    return f"""[RESUME_IMPORT]
ИЗВЛЕКИ СТРУКТУРИРОВАННЫЕ ДАННЫЕ ИЗ ТЕКСТА РЕЗЮМЕ:

---
{resume_text}
---

Верни JSON ТОЧНО по схеме:
{{
  "desiredPosition": string|null,
  "about": string|null,
  "city": string|null,
  "skills": [string, ...],
  "workExperiences": [
    {{
      "companyName": string,
      "position": string,
      "startDate": "YYYY-MM-DD"|null,
      "endDate": "YYYY-MM-DD"|null,
      "isCurrent": bool,
      "description": string|null,
      "skills": [string, ...]
    }}
  ],
  "education": [
    {{
      "institutionName": string,
      "degree": string|null,
      "fieldOfStudy": string|null,
      "startYear": int|null,
      "endYear": int|null,
      "isCurrent": bool,
      "description": string|null
    }}
  ],
  "warnings": [string, ...]
}}

Правила:
- Вывод ТОЛЬКО валидный JSON (без пояснений вне JSON, без лишних ключей). НЕ оборачивай в ```json```.
- Язык извлечённых текстовых полей сохраняй как в исходном резюме.
- desiredPosition: желаемая/целевая должность (headline) или последняя роль, если цель явно не указана.
- about: только если в файле есть блок summary/«о себе». Не генерируй с нуля.
- city: город строкой, как в файле; без id.
- skills: дедуплицированный список навыков из резюме, максимум 30.
  Если навыков больше — оставь самые релевантные для desiredPosition / основного опыта.
  Если нет — [].
- workExperiences: как в файле. Пропускай записи без companyName и position.
- Даты строго YYYY-MM-DD. Неизвестный день → 01. Неизвестный месяц → 01.
- endDate: null, если место работы текущее.
- isCurrent: true только если в резюме явно указано, что работа/учёба продолжается.
- education: записи без institutionName отбрасывай.
- ЗАПРЕЩЕНО выдумывать зарплату, employmentTypes, workFormats и любые поля, которых нет в тексте.
- warnings: только коды из списка (без свободного текста). Если замечаний нет — []:
  "incomplete_dates", "incomplete_education_years", "swapped_experience_dates",
  "swapped_education_years", "truncated_source", "low_confidence_city",
  "ambiguous_current_role", "low_confidence_extraction".
""".strip()
