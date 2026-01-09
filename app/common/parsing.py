import json
import re
from typing import Type, TypeVar, Any

from pydantic import BaseModel, ValidationError

from app.common.errors import UpstreamError

T = TypeVar("T", bound=BaseModel)


def extract_first_json(text: str) -> dict[str, Any]:
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        raw = s
    else:
        match = re.search(r"\{.*\}", s, flags=re.DOTALL)
        if not match:
            raise UpstreamError("Model output did not contain JSON.")
        raw = match.group(0)

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
