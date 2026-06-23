import logging

import httpx

from app.ai.base import LLMClient, LLMInput, LLMResponse
from app.common.errors import UpstreamError
from app.common.retry import retry_async

logger = logging.getLogger(__name__)


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str, *, timeout: int = 60, retry_attempts: int = 3, retry_backoff: float = 1.0) -> None:
        if not api_key:
            raise UpstreamError("GEMINI_API_KEY is not set.")

        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com"
        self.model = model
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff

    async def generate(self, *, inp: LLMInput) -> LLMResponse:
        async def _attempt() -> LLMResponse:
            url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
            payload = {
                "systemInstruction": {"parts": [{"text": inp.system}]},
                "contents": [{"role": "user", "parts": [{"text": inp.user}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.95,
                    "maxOutputTokens": 8_000,
                },
            }

            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(float(self.timeout), connect=10.0)) as client:
                    resp = await client.post(url, params={"key": self.api_key}, json=payload)
            except httpx.RequestError as e:
                raise UpstreamError(f"Gemini request error: {e}") from e

            if resp.status_code in (429, 503, 500):
                raise UpstreamError(f"Gemini transient error {resp.status_code}: {resp.text}")

            if resp.status_code >= 400:
                raise UpstreamError(f"Gemini error {resp.status_code}: {resp.text}")

            raw = resp.json()
            try:
                candidates = raw.get("candidates", [])
                if not candidates:
                    raise UpstreamError("Gemini returned no candidates.")
                parts = candidates[0]["content"].get("parts", [])
                text = (parts[0].get("text") or "").strip()
            except UpstreamError:
                raise
            except Exception as e:
                logger.exception("Failed to parse Gemini response")
                raise UpstreamError(f"Failed to parse Gemini response: {e}") from e

            if not text:
                raise UpstreamError("Gemini returned empty text.")

            return LLMResponse(text=text, raw=raw)

        return await retry_async(
            _attempt,
            attempts=self.retry_attempts,
            backoff_factor=self.retry_backoff,
            operation="Gemini HTTP",
        )
