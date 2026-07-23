import json
from datetime import date

from app.features.profile_boost.schemas import ProfileBoostRequest

_TONE_HINTS = {
    "neutral": "ровный, деловой тон без пафоса",
    "confident": "уверенный тон, акцент на сильных сторонах, без хвастовства",
    "concise": "максимально кратко и по делу, без лишних слов",
}


def system_prompt(version: str) -> str:
    if version != "v1":
        return system_prompt("v1")

    today = date.today().strftime("%d.%m.%Y")
    return (
        f"Сегодняшняя дата: {today}. "
        "Ты помогаешь людям любого профиля — от рабочих и специалистов сферы услуг "
        "до офисных и творческих профессий — улучшить текст резюме. "
        "Пишешь понятно для обычного человека и для рекрутера. "
        "Навыки — это свободные текстовые теги под роль человека, а не IT-таксономия "
        "и не стек разработчика. "
        "Поле specializations — доменный контекст профиля (например «Продажи», «Розничная торговля»). "
        "Используй его как ориентир сферы, не копируй названия специализаций дословно в skills или «О себе». "
        "Если specializations пустой — не выдумывай сферу и не подставляй IT. "
        "Приоритет контекста: желаемая должность и опыт выше, "
        "затем specializations, затем остальные поля. "
        "Опирайся строго на переданные данные. Не выдумывай компании, должности, даты, "
        "цифры, сертификаты, образование и навыки, которых нет во входе. "
        "Не используй шаблонные фразы вроде «ответственный командный игрок», "
        "«стрессоустойчивый» или «нацелен на результат», если на это нет фактов. "
        "Возвращай ТОЛЬКО валидный JSON строго по схеме, без лишних ключей. "
        "НЕ оборачивай ответ в ```json``` — только чистый JSON. "
        "Весь текст в JSON — на языке, указанном в locale."
    )


def user_prompt(*, request: ProfileBoostRequest) -> str:
    opts = request.options
    assert opts is not None
    focus = request.focus
    assert focus is not None

    tone = _TONE_HINTS.get(opts.tone, _TONE_HINTS["neutral"])
    resume_json = json.dumps(
        request.resume.model_dump(exclude_none=True),
        ensure_ascii=False,
        indent=2,
    )
    focus_json = json.dumps(
        focus.model_dump(exclude_none=True),
        ensure_ascii=False,
        indent=2,
    )
    max_chars = opts.maxChars
    variants_n = opts.variants

    target_rules = _target_rules(request.target, request.mode, max_chars)

    return f"""[PROFILE_BOOST]

target: {request.target}
mode: {request.mode}
locale: {request.locale}
tone: {opts.tone} ({tone})
variants: {variants_n}
maxChars: {max_chars if max_chars is not None else "n/a"}

ПРОФИЛЬ КАНДИДАТА (JSON):
{resume_json}

ФОКУС БЛОКА (JSON):
{focus_json}

Верни JSON ТОЧНО по схеме:
{{
  "variants": [
    {{
      "text": "<текст или null>",
      "skills": ["<навык>", ...] | null,
      "addedSkills": ["<навык>", ...] | null,
      "removedSkills": ["<навык>", ...] | null,
      "rationale": "<одно короткое предложение>"
    }}
  ],
  "warnings": ["insufficient_detail"] | []
}}

ОБЩИЕ ПРАВИЛА:
- Вывод ТОЛЬКО валидный JSON. НЕ оборачивай в ```json```.
- Все строки — строго на языке locale={request.locale}.
- Не выдумывай факты вне входа.
- mode=improve: сохрани смысл и факты, улучши формулировки и структуру.
- mode=generate: собери текст только из данных профиля и focus.
- Доменный контекст: сначала desiredPosition и опыт, затем specializations (если не пустой),
  затем остальные поля. specializations — ориентир сферы, не копируй названия дословно
  в skills/about. Если specializations пустой — не выдумывай сферу и не подставляй IT.
- При бедном контексте — короткий текст и warnings: ["insufficient_detail"], без воды.
- variants={variants_n}: верни ровно {variants_n} вариант(а). При 2 — заметно разные формулировки, не копии.
- rationale: одно короткое предложение для UI (почему такой текст/список).
- Не используй сырые имена полей API в тексте (desiredPosition, workExperiences, specializations и т.п.).
  Говори по-человечески: «желаемая должность», «опыт работы», «специализации».

{target_rules}
""".strip()


def _skills_rules(*, baseline: str) -> str:
    return f"""ПРАВИЛА ДЛЯ НАВЫКОВ (skills):
- skills — массив коротких строк-тегов (не markdown, не одно предложение, не список через запятую в text).
- Каждый навык — короткое название под роль (обычно 1–4 слова), длина ≤ 100 символов.
- Не выдумывай навыки вне контекста резюме. Можно обобщать близкие формулировки:
  пример: «работа на кассе» → «Кассовое обслуживание».
- Ориентируйся на домен: должность и опыт важнее, specializations — следующий ориентир сферы
  (не копируй названия specialization дословно в skills). Если specializations пустой —
  не выдумывай сферу и не подставляй IT. Не подставляй IT-стек и IT-дефолты
  (Python, Docker, Agile и т.п.), если этого нет во входе или роль/specializations явно не про IT.
  При пустом или неясном контексте — короткий список только из явных фактов
  + warnings: ["insufficient_detail"], без «универсальных» IT-навыков.
- skills — итоговый рекомендуемый список (до ~30 пунктов).
- addedSkills — что добавить относительно {baseline} (может быть []).
- removedSkills — что убрать или смержить (дубликаты, опечатки, слишком длинные/шумные);
  в improve не удаляй явные навыки пользователя без причины.
- Нормализуй написание без смены смысла (регистр, пробелы, привычные сокращения профессии).
""".strip()


def _target_rules(target: str, mode: str, max_chars: int | None) -> str:
    if target == "about":
        limit = f"Мягкий лимит длины text: ~{max_chars} символов." if max_chars else ""
        return f"""ПРАВИЛА ДЛЯ target=about:
- Заполни поле text. Поля skills/addedSkills/removedSkills оставь null.
- Это блок «О себе»: 2–5 предложений о человеке как о кандидате.
- Пиши строго от первого лица («я», «работаю», «имею»), как текст для своего резюме.
  Запрещено третье лицо и отстранённые формулировки вроде «сотрудник ищет работу»,
  «кандидат имеет опыт», «специалист обладает».
- Опирайся на всё полезное из профиля, если заполнено:
  желаемая должность, опыт работы, specializations (сфера), навыки, образование, город,
  языки (с уровнем владения), сертификаты, портфолио.
- Приоритет опоры: должность и опыт → specializations → остальное.
  specializations — ориентир сферы, не копируй названия дословно.
  Если должность общая, а specializations заполнены — держи текст в этой сфере.
  Если specializations пустой — не выдумывай сферу и не подставляй IT.
- Упоминай языки/сертификаты/портфолио только если они есть во входе и усиливают «О себе»;
  не перечисляй всё подряд — вплетай 1–2 сильных сигнала естественно.
- Пиши для любой профессии естественно: водитель, продавец, повар, учитель, менеджер, врач и т.д.
- Не копируй дословно описания отдельных мест работы.
- Не добавляй метрики и достижения, которых нет во входе.
- {limit}
- mode={mode}.
""".strip()

    if target == "experience":
        limit = f"Мягкий лимит длины text: ~{max_chars} символов." if max_chars else ""
        return f"""ПРАВИЛА ДЛЯ target=experience:
- Заполни поле text — описание одной позиции из focus.experience.
- Каждый пункт с новой строки. НЕ ставь маркеры списка (-, •, *, цифры) — только текст и переносы строк \\n.
- Пиши действия и результаты, по одному смысловому пункту на строку.
- Не клади навыки в text — только в skills / addedSkills / removedSkills.
{_skills_rules(baseline="текущих focus.experience.skills")}
- Используй только факты из focus.experience и релевантный контекст профиля.
- Не копируй блок «О себе» один в один.
- Не придумывай KPI, цифры, инструменты и обязанности, которых нет во входе.
- Формулируй под реальную профессию из данных.
- {limit}
- mode={mode}.
""".strip()

    return f"""ПРАВИЛА ДЛЯ target=skills:
- Поле text оставь null. Навыки только в массивах skills / addedSkills / removedSkills.
{_skills_rules(baseline="текущего resume.skills")}
- mode={mode}.
""".strip()
