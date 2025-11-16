from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    api_gateway_url: str = Field(default="http://localhost:8000")
    default_birth_date: str = Field(default="1990-01-01")
    public_base_url: str = Field(default="", env="TELEGRAM_PUBLIC_BASE_URL")
    bot_username: str = Field(default="", env="BOT_USERNAME")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()