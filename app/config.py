from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = Field(default="cv-ai-microservice", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    # LLM provider selection
    llm_provider: str = Field(default="gemini-http", alias="LLM_PROVIDER")

    # Gemini REST
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_base_url: str = Field(default="https://generativelanguage.googleapis.com", alias="GEMINI_BASE_URL")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # LLM call settings
    llm_timeout: int = Field(default=60, alias="LLM_TIMEOUT")
    llm_retry_attempts: int = Field(default=3, alias="LLM_RETRY_ATTEMPTS")
    llm_retry_backoff_factor: float = Field(default=1.0, alias="LLM_RETRY_BACKOFF_FACTOR")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_hour: int = Field(default=10, alias="RATE_LIMIT_PER_HOUR")

    # Concurrency (per-worker; 0 = disabled)
    max_concurrent_requests: int = Field(default=10, alias="MAX_CONCURRENT_REQUESTS")

    # Resume import (PDF download + text extract)
    pdf_max_pages: int = Field(default=20, alias="PDF_MAX_PAGES")
    pdf_download_timeout: int = Field(default=30, alias="PDF_DOWNLOAD_TIMEOUT")
    pdf_max_size_mb: int = Field(default=10, alias="PDF_MAX_SIZE_MB")
    pdf_download_retries: int = Field(default=3, alias="PDF_DOWNLOAD_RETRIES")
    resume_text_max_chars: int = Field(default=60_000, alias="RESUME_TEXT_MAX_CHARS")
