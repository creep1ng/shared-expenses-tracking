import pytest

from app.core.config import Settings


def test_settings_build_database_and_redis_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "ci")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("API_V1_PREFIX", "/api/v1")
    monkeypatch.setenv("DATABASE_HOST", "db")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "shared_expenses")
    monkeypatch.setenv("DATABASE_USER", "postgres")
    monkeypatch.setenv("DATABASE_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_ECHO", "true")
    monkeypatch.setenv("REDIS_HOST", "redis")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "1")
    monkeypatch.setenv("REDIS_PASSWORD", "redis-secret")
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://minio:9000")
    monkeypatch.setenv("S3_REGION", "us-east-1")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "minio")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "minio-secret")
    monkeypatch.setenv("S3_BUCKET", "receipts")
    monkeypatch.setenv("S3_USE_SSL", "false")
    monkeypatch.setenv("S3_FORCE_PATH_STYLE", "true")
    monkeypatch.setenv("TRANSACTION_RECEIPT_MAX_SIZE_BYTES", "10485760")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "strict")

    settings = Settings.from_env()

    assert settings.database_url == "postgresql+psycopg://postgres:secret@db:5432/shared_expenses"
    assert settings.redis_url == "redis://:redis-secret@redis:6379/1"
    assert settings.s3_endpoint_url == "http://minio:9000"
    assert settings.s3_access_key_id.get_secret_value() == "minio"
    assert settings.s3_secret_access_key.get_secret_value() == "minio-secret"
    assert settings.s3_bucket == "receipts"
    assert settings.s3_use_ssl is False
    assert settings.s3_force_path_style is True
    assert settings.transaction_receipt_max_size_bytes == 10485760
    assert settings.database_echo is True
    assert settings.auth_cookie_secure is True
    assert settings.auth_cookie_samesite == "strict"


def test_settings_allow_empty_redis_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "ci")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("API_V1_PREFIX", "/api/v1")
    monkeypatch.setenv("DATABASE_HOST", "db")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "shared_expenses")
    monkeypatch.setenv("DATABASE_USER", "postgres")
    monkeypatch.setenv("DATABASE_PASSWORD", "secret")
    monkeypatch.setenv("REDIS_HOST", "redis")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")
    monkeypatch.setenv("REDIS_PASSWORD", "")

    settings = Settings.from_env()

    assert settings.redis_url == "redis://redis:6379/0"
