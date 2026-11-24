from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/atendeai.db"

    ai_provider: str = "openai_compatible"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = ""
    ai_timeout: float = Field(default=90, gt=0, le=180)
    ai_max_retries: int = Field(default=2, ge=0, le=3)
    ai_confidence_threshold: float = Field(default=0.70, ge=0, le=1)

    n8n_webhook_url: str = ""
    n8n_api_token: str = ""
    n8n_timeout: float = Field(default=30, gt=0, le=180)
    internal_api_token: str = ""
    frontend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
