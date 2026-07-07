import json
import re
from typing import Type, TypeVar, Any

from pydantic import BaseModel, ValidationError

from app.common.errors import UpstreamError

T = TypeVar("T", bound=BaseModel)

_CONTROL_CHAR_ESCAPES: dict[str, str] = {
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
    "\b": "\\b",
    "\f": "\\f",
}


def _escape_control_chars_in_strings(text: str) -> str:
    """Заменяет буквальные управляющие символы на их JSON-escape внутри строковых значений.

    Модели иногда вставляют реальный символ новой строки вместо \\n прямо
    в тело JSON-строки, что нарушает стандарт JSON. Функция проходит по тексту
    конечным автоматом: вне строк — не трогает ничего, внутри строк — экранирует.
    """
    result: list[str] = []
    in_string = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and in_string:
            result.append(c)
            i += 1
            if i < len(text):
                result.append(text[i])
                i += 1
            continue
        if c == '"':
            in_string = not in_string
            result.append(c)
        elif in_string and c in _CONTROL_CHAR_ESCAPES:
            result.append(_CONTROL_CHAR_ESCAPES[c])
        else:
            result.append(c)
        i += 1
    return "".join(result)


def extract_first_json(text: str) -> dict[str, Any]:
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        raw = s
    else:
        match = re.search(r"\{.*\}", s, flags=re.DOTALL)
        if not match:
            raise UpstreamError("Model output did not contain JSON.")
        raw = match.group(0)

    raw = _escape_control_chars_in_strings(raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise UpstreamError(f"Invalid JSON from model: {e}") from e


def parse_model_output(
    text: str,
    schema: Type[T],
) -> T:
    data = extract_first_json(text)

    try:
        return schema.model_validate(data)
    except ValidationError as e:
        raise UpstreamError(
            f"Model output did not match schema {schema.__name__}: {e}"
        ) from e
