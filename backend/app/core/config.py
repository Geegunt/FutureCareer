from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'VibeCode IDE API'
    api_v1_str: str = '/api'
    secret_key: str
    access_token_expire_minutes: int = 60

    database_url: str

    smtp_host: str = 'localhost'
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = 'ide@vibecode.local'
    smtp_tls: bool = False

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


