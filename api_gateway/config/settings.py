from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = Field(default="change-me", env="API_JWT_SECRET")
    access_token_exp_minutes: int = Field(default=60, ge=5, le=24 * 60)
    user_service_url: HttpUrl = Field(default="https://seasonally-dapper-anaconda.cloudpub.ru/")
    chat_service_url: HttpUrl = Field(default="https://shapelessly-welcomed-roller.cloudpub.ru/")
    payment_service_url: HttpUrl = Field(default="https://vehemently-purifying-lungfish.cloudpub.ru/")
    # Опциональный публичный базовый URL (для генерации ссылок, доступных из браузера)
    public_base_url: str = Field(default="", env="API_PUBLIC_BASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
