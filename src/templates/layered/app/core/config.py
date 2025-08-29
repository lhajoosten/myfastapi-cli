from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "{{project_name}}"
    secret_key: str = "{{secret_key}}"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
