import logging
import httpx

from app.ai.base import LLMClient, LLMInput, LLMResponse
from app.common.errors import UpstreamError
from app.common.pdf import extract_text_from_pdf

logger = logging.getLogger(__name__)


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise UpstreamError("GEMINI_API_KEY is not set.")

        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com"
        self.model = model

    def _files_to_text(self, files) -> str:
        texts: list[str] = []

        for f in files:
            if f.mime_type == "application/pdf":
                texts.append(
                    extract_text_from_pdf(
                        f.content,
                        max_pages=10,
                    )
                )
            else:
                raise UpstreamError(
                    f"Unsupported file type for Gemini REST: {f.mime_type}"
                )

        return "\n\n".join(texts)

    async def generate(self, inp: LLMInput) -> LLMResponse:
        user_text = inp.user

        if inp.files:
            extracted = self._files_to_text(inp.files)
            user_text = f"{user_text}\n\n\n\n--- CV CONTENT ---\n\n{extracted}"

        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        print("\n\n\n")
        print(f"system message: {inp.system}")
        print(f"prompt: {user_text}")
        print("\n\n\n")

        payload = {
            "systemInstruction": {
                "parts": [{"text": inp.system}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_text}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "maxOutputTokens": 5_000,
            },
        }

        timeout = httpx.Timeout(60.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.post(url, params=params, json=payload)
            except httpx.RequestError as e:
                raise UpstreamError(f"Gemini request error: {e}") from e

        if resp.status_code >= 400:
            raise UpstreamError(f"Gemini error {resp.status_code}: {resp.text}")

        raw = resp.json()

        try:
            candidates = raw.get("candidates", [])
            if not candidates:
                raise UpstreamError("Gemini returned no candidates.")

            parts = candidates[0]["content"].get("parts", [])
            text = (parts[0].get("text") or "").strip()

        except Exception as e:
            logger.exception("Failed to parse Gemini response")
            raise UpstreamError(f"Failed to parse Gemini response: {e}") from e

        if not text:
            raise UpstreamError("Gemini returned empty text.")

        return LLMResponse(text=text, raw=raw)
