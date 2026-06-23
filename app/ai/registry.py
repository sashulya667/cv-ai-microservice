from app.ai.base import LLMClient
from app.ai.providers.gemini_http import GeminiClient
from app.ai.providers.gemini_sdk import GeminiSDKClient
from app.ai.providers.mock import MockClient
from app.common.errors import BadRequest
from app.config import Settings


class LLMRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get(self, provider: str) -> LLMClient:
        name = provider.strip().lower()

        if name == "gemini-http":
            return GeminiClient(
                api_key=self.settings.gemini_api_key,
                model=self.settings.gemini_model,
                timeout=self.settings.llm_timeout,
                retry_attempts=self.settings.llm_retry_attempts,
                retry_backoff=self.settings.llm_retry_backoff_factor,
            )

        if name == "gemini-sdk":
            return GeminiSDKClient(
                api_key=self.settings.gemini_api_key,
                model=self.settings.gemini_model,
                timeout=self.settings.llm_timeout,
                retry_attempts=self.settings.llm_retry_attempts,
                retry_backoff=self.settings.llm_retry_backoff_factor,
            )

        if name == "mock":
            return MockClient()

        raise BadRequest(f"Unknown LLM provider: {provider}")
