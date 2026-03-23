from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies.auth import _TEST_REDIS
from app.core.config import get_settings
from app.core.time import utc_now
from app.db.base import Base
from app.db.models import WorkspaceInvitation
from app.db.session import get_db_session
from app.main import create_app


@pytest.fixture
def workspace_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "workspace.db"
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
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("WORKSPACE_INVITATION_TTL_SECONDS", "3600")

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


def test_unauthenticated_workspace_access_is_rejected(workspace_client: TestClient) -> None:
    response = workspace_client.get("/api/v1/workspaces")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_owner_can_update_workspace_settings(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Casa", workspace_type="shared")

    response = owner_client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        json={"name": "Finanzas Familiares"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Finanzas Familiares"
    assert response.json()["current_user_role"] == "owner"


def test_member_cannot_update_workspace_settings(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(workspace_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Compartido", workspace_type="shared")
    invitation_token = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )["invitation_token"]
    accept_response = member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation_token},
    )
    assert accept_response.status_code == 200

    response = member_client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        json={"name": "Intento no permitido"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Only workspace owners can perform this action."}


def test_member_can_view_shared_workspace(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(workspace_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Viaje", workspace_type="shared")
    invitation_token = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )["invitation_token"]

    accept_response = member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation_token},
    )
    details_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}")

    assert accept_response.status_code == 200
    assert details_response.status_code == 200
    assert details_response.json()["id"] == workspace["id"]
    assert details_response.json()["current_user_role"] == "member"
    assert details_response.json()["member_count"] == 2


def test_non_member_is_rejected_from_workspace(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    outsider_client = _sign_up_and_sign_in(workspace_client, "outsider@example.com")
    workspace = _create_workspace(owner_client, name="Privado", workspace_type="shared")

    response = outsider_client.get(f"/api/v1/workspaces/{workspace['id']}")

    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have access to this workspace."}


def test_owner_can_manage_invitations(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(workspace_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Hogar", workspace_type="shared")

    create_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/invitations",
        json={"email": "member@example.com"},
    )
    invitation_id = create_response.json()["id"]
    list_response = owner_client.get(f"/api/v1/workspaces/{workspace['id']}/invitations")
    member_list_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/invitations")
    revoke_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/invitations/{invitation_id}/revoke"
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "pending"
    assert create_response.json()["invitation_token"]
    assert list_response.status_code == 200
    assert len(list_response.json()["invitations"]) == 1
    assert member_list_response.status_code == 403
    assert member_list_response.json() == {"detail": "You do not have access to this workspace."}
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"


def test_invitation_acceptance_creates_membership(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(workspace_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Proyecto", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )

    accept_response = member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    members_response = owner_client.get(f"/api/v1/workspaces/{workspace['id']}/members")
    workspaces_response = member_client.get("/api/v1/workspaces")

    assert accept_response.status_code == 200
    assert accept_response.json()["workspace"]["current_user_role"] == "member"
    assert members_response.status_code == 200
    assert [member["email"] for member in members_response.json()["members"]] == [
        "owner@example.com",
        "member@example.com",
    ]
    assert workspaces_response.status_code == 200
    assert workspaces_response.json()["workspaces"][0]["id"] == workspace["id"]


def test_invalid_or_expired_invitation_is_rejected(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(workspace_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Viaje", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    _expire_invitation(workspace_client, UUID(invitation["id"]))

    expired_response = member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    invalid_response = member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": "invalid-invitation-token-value"},
    )

    assert expired_response.status_code == 409
    assert expired_response.json() == {"detail": "Invitation has expired."}
    assert invalid_response.status_code == 400
    assert invalid_response.json() == {"detail": "Invitation token is invalid."}


def test_duplicate_invitation_conflict_is_explicit(workspace_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(workspace_client, "owner@example.com")
    _sign_up_and_sign_in(workspace_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Equipo", workspace_type="shared")

    first_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/invitations",
        json={"email": "member@example.com"},
    )
    duplicate_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/invitations",
        json={"email": "member@example.com"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "A pending invitation for that email already exists."
    }


def _sign_up_and_sign_in(client: TestClient, email: str) -> TestClient:
    session_client = TestClient(cast(FastAPI, client.app))
    response = session_client.post(
        "/api/v1/auth/sign-up",
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 201
    response = session_client.post(
        "/api/v1/auth/sign-in",
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 200
    return session_client


def _create_workspace(client: TestClient, *, name: str, workspace_type: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "type": workspace_type},
    )
    assert response.status_code == 201
    return cast(dict[str, str], response.json())


def _create_invitation(client: TestClient, *, workspace_id: str, email: str) -> dict[str, str]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": email},
    )
    assert response.status_code == 201
    return cast(dict[str, str], response.json())


def _expire_invitation(client: TestClient, invitation_id: UUID) -> None:
    app = cast(FastAPI, client.app)
    session_factory = app.dependency_overrides[get_db_session]
    session_generator = session_factory()
    session = next(session_generator)
    try:
        invitation = session.scalar(
            select(WorkspaceInvitation).where(WorkspaceInvitation.id == invitation_id)
        )
        assert invitation is not None
        invitation.expires_at = utc_now() - timedelta(minutes=1)
        session.add(invitation)
        session.commit()
    finally:
        session.close()
        session_generator.close()
