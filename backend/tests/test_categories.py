from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies.auth import _TEST_REDIS
from app.core.config import get_settings
from app.db.base import Base
from app.db.models import User, Workspace, WorkspaceMember, WorkspaceMemberRole, WorkspaceType
from app.db.session import get_db_session
from app.main import create_app
from app.repositories.categories import CategoryRepository


@pytest.fixture
def categories_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "categories.db"
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


def test_unauthenticated_category_access_is_rejected(categories_client: TestClient) -> None:
    response = categories_client.get(
        "/api/v1/workspaces/00000000-0000-0000-0000-000000000000/categories"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_workspace_creation_seeds_default_categories(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Casa", workspace_type="personal")

    response = owner_client.get(f"/api/v1/workspaces/{workspace['id']}/categories")

    assert response.status_code == 200
    categories = response.json()["categories"]
    assert len(categories) == 12
    assert {category["type"] for category in categories} == {"income", "expense"}
    assert any(category["name"] == "Comida" for category in categories)
    assert any(category["name"] == "Gastos financieros" for category in categories)
    assert all(category["archived_at"] is None for category in categories)


def test_member_can_create_update_and_archive_categories(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(categories_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Casa", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    accept_response = member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    assert accept_response.status_code == 200

    create_response = member_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories",
        json={
            "name": "Mascotas",
            "type": "expense",
            "icon": "paw-print",
            "color": "#84CC16",
        },
    )
    created_category = create_response.json()

    update_response = member_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/categories/{created_category['id']}",
        json={
            "name": "Veterinaria",
            "icon": "stethoscope",
            "color": "#16A34A",
        },
    )
    archive_response = member_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories/{created_category['id']}/archive"
    )
    active_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/categories")
    all_response = member_client.get(
        f"/api/v1/workspaces/{workspace['id']}/categories?include_archived=true"
    )

    assert create_response.status_code == 201
    assert created_category["name"] == "Mascotas"
    assert created_category["type"] == "expense"
    assert created_category["icon"] == "paw-print"
    assert created_category["color"] == "#84CC16"

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Veterinaria"
    assert update_response.json()["icon"] == "stethoscope"
    assert update_response.json()["color"] == "#16A34A"

    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True
    assert archive_response.json()["archived_at"] is not None
    assert active_response.status_code == 200
    active_names = {category["name"] for category in active_response.json()["categories"]}
    assert "Veterinaria" not in active_names
    assert all_response.status_code == 200
    assert any(category["name"] == "Veterinaria" for category in all_response.json()["categories"])


def test_duplicate_active_category_name_is_scoped_by_type(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Duplicados", workspace_type="personal")

    first_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories",
        json={
            "name": "Bonus",
            "type": "income",
            "icon": "badge-dollar-sign",
            "color": "#15803D",
        },
    )
    duplicate_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories",
        json={
            "name": " bonus ",
            "type": "income",
            "icon": "wallet",
            "color": "#16A34A",
        },
    )
    different_type_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories",
        json={
            "name": "Bonus",
            "type": "expense",
            "icon": "receipt",
            "color": "#DC2626",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "An active category with that type and name already exists in this workspace."
    }
    assert different_type_response.status_code == 201


def test_archived_category_name_can_be_reused(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Archivo", workspace_type="personal")
    category = _create_category(
        owner_client,
        workspace_id=workspace["id"],
        name="Temporal",
        category_type="expense",
        icon="archive",
        color="#6B7280",
    )

    archive_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories/{category['id']}/archive"
    )
    reused_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories",
        json={
            "name": "Temporal",
            "type": "expense",
            "icon": "archive-restore",
            "color": "#4B5563",
        },
    )

    assert archive_response.status_code == 200
    assert reused_response.status_code == 201
    assert reused_response.json()["name"] == "Temporal"


def test_workspace_isolation_and_non_member_access_are_enforced(
    categories_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    outsider_client = _sign_up_and_sign_in(categories_client, "outsider@example.com")
    workspace = _create_workspace(owner_client, name="Privado", workspace_type="shared")
    category = _create_category(
        owner_client,
        workspace_id=workspace["id"],
        name="Reservado",
        category_type="expense",
        icon="lock",
        color="#111827",
    )
    outsider_workspace = _create_workspace(
        outsider_client,
        name="Ajeno",
        workspace_type="personal",
    )

    list_response = outsider_client.get(f"/api/v1/workspaces/{workspace['id']}/categories")
    update_response = outsider_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/categories/{category['id']}",
        json={"name": "Intrusion"},
    )
    cross_workspace_response = owner_client.patch(
        f"/api/v1/workspaces/{outsider_workspace['id']}/categories/{category['id']}",
        json={"name": "Wrong workspace"},
    )

    assert list_response.status_code == 403
    assert list_response.json() == {"detail": "You do not have access to this workspace."}
    assert update_response.status_code == 403
    assert update_response.json() == {"detail": "You do not have access to this workspace."}
    assert cross_workspace_response.status_code == 403
    assert cross_workspace_response.json() == {
        "detail": "You do not have access to this workspace."
    }


def test_category_not_found_is_scoped_to_workspace(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    another_client = _sign_up_and_sign_in(categories_client, "another@example.com")
    workspace = _create_workspace(owner_client, name="Casa", workspace_type="personal")
    other_workspace = _create_workspace(another_client, name="Otro", workspace_type="personal")
    category = _create_category(
        another_client,
        workspace_id=other_workspace["id"],
        name="Externa",
        category_type="expense",
        icon="globe",
        color="#2563EB",
    )

    response = owner_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/categories/{category['id']}",
        json={"name": "No existe"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found."}


def test_archived_category_cannot_be_updated(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Historial", workspace_type="personal")
    category = _create_category(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja vieja",
        category_type="expense",
        icon="box",
        color="#92400E",
    )
    archive_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/categories/{category['id']}/archive"
    )
    assert archive_response.status_code == 200

    update_response = owner_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/categories/{category['id']}",
        json={"name": "Caja nueva"},
    )

    assert update_response.status_code == 409
    assert update_response.json() == {"detail": "Archived categories cannot be updated."}


def test_default_category_backfill_is_idempotent(categories_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(categories_client, "owner@example.com")
    app = cast(FastAPI, categories_client.app)
    session_factory = app.dependency_overrides[get_db_session]
    session_generator = session_factory()
    session = next(session_generator)
    try:
        owner = session.scalar(select(User).where(User.email == "owner@example.com"))
        assert owner is not None

        workspace = Workspace(
            name="Legacy",
            type=WorkspaceType.PERSONAL,
            created_by_user_id=owner.id,
        )
        session.add(workspace)
        session.flush()
        session.add(
            WorkspaceMember(
                workspace_id=workspace.id,
                user_id=owner.id,
                role=WorkspaceMemberRole.OWNER,
            )
        )
        session.commit()
        workspace_id = str(workspace.id)

        repository = CategoryRepository(session)
        first_batch = repository.ensure_default_categories_for_workspace(workspace_id=workspace.id)
        second_batch = repository.ensure_default_categories_for_workspace(workspace_id=workspace.id)
        session.commit()

        assert len(first_batch) == 12
        assert second_batch == []
    finally:
        session.close()
        session_generator.close()

    response = owner_client.get(f"/api/v1/workspaces/{workspace_id}/categories")

    assert response.status_code == 200
    assert len(response.json()["categories"]) == 12


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


def _create_category(
    client: TestClient,
    *,
    workspace_id: str,
    name: str,
    category_type: str,
    icon: str,
    color: str,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/categories",
        json={
            "name": name,
            "type": category_type,
            "icon": icon,
            "color": color,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())
