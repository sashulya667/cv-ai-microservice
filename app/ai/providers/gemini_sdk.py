import asyncio
import tempfile
from pathlib import Path

from google import genai

from app.ai.base import LLMClient, LLMInput, LLMResponse
from app.common.errors import UpstreamError


class GeminiSDKClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise UpstreamError("GEMINI_API_KEY is not set.")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(self, *, inp: LLMInput) -> LLMResponse:
        def _call():
            contents = []

            temp_files: list[Path] = []

            try:
                if inp.files:
                    for f in inp.files:
                        suffix = Path(f.filename).suffix or ".pdf"

                        with tempfile.NamedTemporaryFile(
                            suffix=suffix,
                            delete=False,
                        ) as tmp:
                            tmp.write(f.content)
                            tmp_path = Path(tmp.name)

                        temp_files.append(tmp_path)

                        uploaded = self.client.files.upload(
                            file=str(tmp_path)
                        )
                        contents.append(uploaded)
                    contents.append("\n\nФайл CV был приложен. Проанализируй его содержимое.\n\n")

                contents.append(
                    inp.system
                    + "\n\n"
                    + inp.user
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                )

                return response

            finally:
                for p in temp_files:
                    try:
                        p.unlink()
                    except Exception:
                        pass

        try:
            resp = await asyncio.to_thread(_call)
        except Exception as e:
            raise UpstreamError(f"Gemini SDK error: {e}") from e

        text = getattr(resp, "text", None)
        if not text:
            raise UpstreamError("Gemini SDK returned empty response.")

        return LLMResponse(text=text, raw=resp)
