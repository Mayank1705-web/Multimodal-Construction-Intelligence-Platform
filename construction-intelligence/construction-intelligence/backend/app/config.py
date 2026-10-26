from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "mock"  # mock | anthropic | bedrock
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = ""

    cors_origins: str = "http://localhost:5173"
    data_dir: str = "./data"
    max_image_mb: int = 8
    max_images_per_request: int = 4
    llm_timeout_seconds: int = 90

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
