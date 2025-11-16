from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gigachat_key: str = Field(default="", env="GIGACHAT_KEY")
    gigachat_auth_endpoint: str = Field(
        default="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        env="GIGACHAT_AUTH_ENDPOINT",
    )
    gigachat_endpoint: str = Field(
        default="https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        env="GIGACHAT_ENDPOINT",
    )
    gigachat_scope: str = Field(
        default="GIGACHAT_API_PERS",
        env="GIGACHAT_SCOPE",
    )
    redis_url: str | None = Field(default=None, env="CHAT_REDIS_URL")
    empathy_temperature: float = Field(default=0.35, ge=0.0, le=1.0)
    max_context_messages: int = Field(default=5, ge=1, le=20)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
