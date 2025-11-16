from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg2://dream:dream@postgres:5432/dream",
        env="PAYMENT_DATABASE_URL",
    )
    api_gateway_url: AnyHttpUrl = Field(
        default="https://unequally-paternal-guan.cloudpub.ru/",
        env="API_GATEWAY_URL",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
