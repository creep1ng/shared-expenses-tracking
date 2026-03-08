from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies.auth import _TEST_REDIS
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app


@pytest.fixture
def auth_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "auth.db"
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("API_V1_PREFIX", "/api/v1")
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "shared_expenses_test")
    monkeypatch.setenv("DATABASE_USER", "postgres")
    monkeypatch.setenv("DATABASE_PASSWORD", "postgres")
    monkeypatch.setenv("DATABASE_ECHO", "false")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")
    monkeypatch.setenv("REDIS_PASSWORD", "")
    monkeypatch.setenv("AUTH_ENABLE_DEV_RESET_TOKEN_RESPONSE", "true")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")

    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    _TEST_REDIS._values.clear()

    app = create_app(settings)

    def override_db_session() -> Generator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_sign_up_sign_in_and_session_persistence(auth_client: TestClient) -> None:
    sign_up_response = auth_client.post(
        "/api/v1/auth/sign-up",
        json={"email": "user@example.com", "password": "secret123"},
    )

    assert sign_up_response.status_code == 201
    assert sign_up_response.json()["email"] == "user@example.com"

    sign_in_response = auth_client.post(
        "/api/v1/auth/sign-in",
        json={"email": "user@example.com", "password": "secret123"},
    )

    assert sign_in_response.status_code == 200
    assert "shared_expenses_session" in sign_in_response.cookies

    current_user_response = auth_client.get("/api/v1/auth/me")

    assert current_user_response.status_code == 200
    assert current_user_response.json()["user"]["email"] == "user@example.com"


def test_invalid_credentials_are_rejected(auth_client: TestClient) -> None:
    auth_client.post(
        "/api/v1/auth/sign-up",
        json={"email": "user@example.com", "password": "secret123"},
    )

    response = auth_client.post(
        "/api/v1/auth/sign-in",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password."}


def test_protected_endpoint_rejects_unauthenticated_requests(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_sign_out_clears_session(auth_client: TestClient) -> None:
    auth_client.post(
        "/api/v1/auth/sign-up",
        json={"email": "user@example.com", "password": "secret123"},
    )
    auth_client.post(
        "/api/v1/auth/sign-in",
        json={"email": "user@example.com", "password": "secret123"},
    )

    sign_out_response = auth_client.post("/api/v1/auth/sign-out")
    current_user_response = auth_client.get("/api/v1/auth/me")

    assert sign_out_response.status_code == 200
    assert current_user_response.status_code == 401


def test_password_reset_flow_rotates_password(auth_client: TestClient) -> None:
    auth_client.post(
        "/api/v1/auth/sign-up",
        json={"email": "user@example.com", "password": "secret123"},
    )

    request_response = auth_client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    reset_token = request_response.json()["reset_token"]

    assert request_response.status_code == 200
    assert isinstance(reset_token, str)

    confirm_response = auth_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "new-secret123"},
    )
    old_password_response = auth_client.post(
        "/api/v1/auth/sign-in",
        json={"email": "user@example.com", "password": "secret123"},
    )
    new_password_response = auth_client.post(
        "/api/v1/auth/sign-in",
        json={"email": "user@example.com", "password": "new-secret123"},
    )

    assert confirm_response.status_code == 200
    assert old_password_response.status_code == 401
    assert new_password_response.status_code == 200


def test_duplicate_sign_up_is_rejected(auth_client: TestClient) -> None:
    auth_client.post(
        "/api/v1/auth/sign-up",
        json={"email": "user@example.com", "password": "secret123"},
    )

    response = auth_client.post(
        "/api/v1/auth/sign-up",
        json={"email": "user@example.com", "password": "secret123"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "A user with that email already exists."}
