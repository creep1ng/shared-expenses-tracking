from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "ci", "staging", "production"] | str = Field(
        default="development",
        alias="APP_ENV",
    )
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    database_host: str = Field(alias="DATABASE_HOST")
    database_port: int = Field(default=5432, alias="DATABASE_PORT")
    database_name: str = Field(alias="DATABASE_NAME")
    database_user: str = Field(alias="DATABASE_USER")
    database_password: SecretStr = Field(alias="DATABASE_PASSWORD")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: SecretStr | None = Field(default=None, alias="REDIS_PASSWORD")

    @property
    def database_url(self) -> str:
        password = self.database_password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.database_user}:{password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password is None or self.redis_password.get_secret_value() == "":
            auth_segment = ""
        else:
            auth_segment = f":{self.redis_password.get_secret_value()}@"

        return f"redis://{auth_segment}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @classmethod
    def from_env(cls, **values: Any) -> "Settings":
        return cls(**values)


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
