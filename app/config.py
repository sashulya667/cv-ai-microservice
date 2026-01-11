from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = Field(default="cv-ai-microservice", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    # LLM provider selection
    llm_provider: str = Field(default="gemini-sdk", alias="LLM_PROVIDER")

    # Gemini REST
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_base_url: str = Field(default="https://generativelanguage.googleapis.com", alias="GEMINI_BASE_URL")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    # HTTP Client settings
    http_timeout: int = Field(default=30, alias="HTTP_TIMEOUT")
    http_max_file_size_mb: int = Field(default=10, alias="HTTP_MAX_FILE_SIZE_MB")
    http_retry_attempts: int = Field(default=3, alias="HTTP_RETRY_ATTEMPTS")
    http_retry_backoff_factor: float = Field(default=0.5, alias="HTTP_RETRY_BACKOFF_FACTOR")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_hour: int = Field(default=10, alias="RATE_LIMIT_PER_HOUR")