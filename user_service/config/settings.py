from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg2://dream:dream@postgres:5432/dream",
        env="USER_DATABASE_URL",
    )
    service_name: str = Field(default="User Service")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
