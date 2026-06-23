import asyncio
import logging
import tempfile
from pathlib import Path

from google import genai

from app.ai.base import LLMClient, LLMInput, LLMResponse
from app.common.errors import UpstreamError
from app.common.retry import retry_async

logger = logging.getLogger(__name__)


class GeminiSDKClient(LLMClient):
    def __init__(self, api_key: str, model: str, *, timeout: int = 60, retry_attempts: int = 3, retry_backoff: float = 1.0) -> None:
        if not api_key:
            raise UpstreamError("GEMINI_API_KEY is not set.")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff

    async def generate(self, *, inp: LLMInput) -> LLMResponse:
        async def _attempt() -> LLMResponse:
            def _call():
                temp_files: list[Path] = []
                try:
                    contents = []
                    if inp.files:
                        for f in inp.files:
                            suffix = Path(f.filename).suffix or ".pdf"
                            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                                tmp.write(f.content)
                                tmp_path = Path(tmp.name)
                            temp_files.append(tmp_path)
                            contents.append(self.client.files.upload(file=str(tmp_path)))

                    contents.append(inp.system + "\n\n" + inp.user)
                    return self.client.models.generate_content(model=self.model, contents=contents)
                finally:
                    for p in temp_files:
                        try:
                            p.unlink()
                        except Exception:
                            pass

            try:
                resp = await asyncio.wait_for(
                    asyncio.to_thread(_call),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("Gemini SDK timed out after %ds", self.timeout)
                raise UpstreamError(f"Gemini SDK timeout after {self.timeout}s")
            except Exception as e:
                logger.warning("Gemini SDK call failed: %s: %s", type(e).__name__, e)
                raise UpstreamError(f"Gemini SDK error: {e}") from e

            text = getattr(resp, "text", None)
            if not text:
                logger.warning("Gemini SDK returned empty response; raw=%r", resp)
                raise UpstreamError("Gemini SDK returned empty response.")

            return LLMResponse(text=text, raw=resp)

        return await retry_async(
            _attempt,
            attempts=self.retry_attempts,
            backoff_factor=self.retry_backoff,
            operation="Gemini SDK",
        )
