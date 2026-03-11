from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "ci", "staging", "production"] | str = Field(
        default="development",
        alias="APP_ENV",
    )
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=5432, alias="DATABASE_PORT")
    database_name: str = Field(default="shared_expenses", alias="DATABASE_NAME")
    database_user: str = Field(default="postgres", alias="DATABASE_USER")
    database_password: SecretStr = Field(default=SecretStr("postgres"), alias="DATABASE_PASSWORD")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: SecretStr | None = Field(default=None, alias="REDIS_PASSWORD")

    s3_endpoint_url: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT_URL")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_access_key_id: SecretStr = Field(default=SecretStr("minioadmin"), alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: SecretStr = Field(
        default=SecretStr("minioadmin"), alias="S3_SECRET_ACCESS_KEY"
    )
    s3_bucket: str = Field(default="transaction-receipts", alias="S3_BUCKET")
    s3_use_ssl: bool = Field(default=False, alias="S3_USE_SSL")
    s3_force_path_style: bool = Field(default=True, alias="S3_FORCE_PATH_STYLE")
    transaction_receipt_max_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        alias="TRANSACTION_RECEIPT_MAX_SIZE_BYTES",
    )

    auth_cookie_name: str = Field(default="shared_expenses_session", alias="AUTH_COOKIE_NAME")
    auth_cookie_domain: str | None = Field(default=None, alias="AUTH_COOKIE_DOMAIN")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        alias="AUTH_COOKIE_SAMESITE",
    )
    auth_session_ttl_seconds: int = Field(
        default=60 * 60 * 24 * 7, alias="AUTH_SESSION_TTL_SECONDS"
    )
    auth_password_min_length: int = Field(default=8, alias="AUTH_PASSWORD_MIN_LENGTH")
    auth_reset_token_ttl_seconds: int = Field(
        default=60 * 60,
        alias="AUTH_RESET_TOKEN_TTL_SECONDS",
    )
    auth_reset_token_pepper: SecretStr = Field(
        default=SecretStr("development-reset-token-pepper"),
        alias="AUTH_RESET_TOKEN_PEPPER",
    )
    auth_password_pepper: SecretStr = Field(
        default=SecretStr("development-password-pepper"),
        alias="AUTH_PASSWORD_PEPPER",
    )
    auth_enable_dev_reset_token_response: bool = Field(
        default=True,
        alias="AUTH_ENABLE_DEV_RESET_TOKEN_RESPONSE",
    )
    workspace_invitation_ttl_seconds: int = Field(
        default=60 * 60 * 24 * 7,
        alias="WORKSPACE_INVITATION_TTL_SECONDS",
    )
    workspace_invitation_token_pepper: SecretStr = Field(
        default=SecretStr("development-workspace-invitation-pepper"),
        alias="WORKSPACE_INVITATION_TOKEN_PEPPER",
    )

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

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @classmethod
    def from_env(cls, **values: Any) -> "Settings":
        return cls(**values)


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
