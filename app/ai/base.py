from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class LLMFile:
    filename: str
    mime_type: str
    content: bytes


@dataclass(frozen=True)
class LLMInput:
    system: str
    user: str
    files: Optional[Sequence[LLMFile]] = None


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: object


class LLMClient:
    async def generate(self, *, inp: LLMInput) -> LLMResponse:
        raise NotImplementedError
