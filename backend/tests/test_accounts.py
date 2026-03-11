from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies.auth import _TEST_REDIS
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app


@pytest.fixture
def accounts_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "accounts.db"
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


def test_unauthenticated_account_access_is_rejected(accounts_client: TestClient) -> None:
    response = accounts_client.get(
        "/api/v1/workspaces/00000000-0000-0000-0000-000000000000/accounts"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_member_can_create_and_list_accounts(accounts_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(accounts_client, "member@example.com")
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
        f"/api/v1/workspaces/{workspace['id']}/accounts",
        json={
            "name": "Cuenta Principal",
            "type": "bank_account",
            "currency": "ars",
            "initial_balance_minor": 125000,
            "description": "Cuenta sueldo",
        },
    )
    list_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")

    assert create_response.status_code == 201
    created_account = create_response.json()
    assert created_account["name"] == "Cuenta Principal"
    assert created_account["type"] == "bank_account"
    assert created_account["currency"] == "ARS"
    assert created_account["initial_balance_minor"] == 125000
    assert created_account["current_balance_minor"] == 125000
    assert created_account["description"] == "Cuenta sueldo"
    assert created_account["archived_at"] is None
    assert created_account["is_archived"] is False

    assert list_response.status_code == 200
    assert [account["id"] for account in list_response.json()["accounts"]] == [
        created_account["id"]
    ]


def test_account_update_changes_initial_and_current_balance(accounts_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Finanzas", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Efectivo",
        account_type="cash",
        currency="usd",
        initial_balance_minor=1000,
        description="Caja chica",
    )

    response = owner_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}",
        json={
            "name": "Efectivo diario",
            "type": "savings_account",
            "initial_balance_minor": 1500,
            "description": "Uso cotidiano",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Efectivo diario"
    assert payload["type"] == "savings_account"
    assert payload["currency"] == "USD"
    assert payload["initial_balance_minor"] == 1500
    assert payload["current_balance_minor"] == 1500
    assert payload["description"] == "Uso cotidiano"


def test_archived_account_is_hidden_by_default_and_name_can_be_reused(
    accounts_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Ahorros", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Banco Nación",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=100,
        description=None,
    )

    archive_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}/archive"
    )
    active_list_response = owner_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")
    all_list_response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/accounts?include_archived=true"
    )
    reused_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/accounts",
        json={
            "name": "Banco Nación",
            "type": "savings_account",
            "currency": "ARS",
            "initial_balance_minor": 200,
            "description": None,
        },
    )

    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True
    assert archive_response.json()["archived_at"] is not None
    assert active_list_response.status_code == 200
    assert active_list_response.json()["accounts"] == []
    assert all_list_response.status_code == 200
    assert len(all_list_response.json()["accounts"]) == 1
    assert reused_response.status_code == 201
    assert reused_response.json()["name"] == "Banco Nación"


def test_duplicate_active_account_name_is_rejected(accounts_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Duplicados", workspace_type="personal")
    first_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/accounts",
        json={
            "name": "Tarjeta Visa",
            "type": "credit_card",
            "currency": "ARS",
            "initial_balance_minor": 0,
            "description": None,
        },
    )
    duplicate_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/accounts",
        json={
            "name": " tarjeta visa ",
            "type": "credit_card",
            "currency": "ARS",
            "initial_balance_minor": 0,
            "description": None,
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "An active account with that name already exists in this workspace."
    }


def test_workspace_isolation_and_non_member_access_are_enforced(
    accounts_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    outsider_client = _sign_up_and_sign_in(accounts_client, "outsider@example.com")
    workspace = _create_workspace(owner_client, name="Privado", workspace_type="shared")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta Reservada",
        account_type="bank_account",
        currency="EUR",
        initial_balance_minor=500,
        description=None,
    )
    outsider_workspace = _create_workspace(
        outsider_client,
        name="Ajeno",
        workspace_type="personal",
    )

    list_response = outsider_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")
    update_response = outsider_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}",
        json={"name": "Intrusion"},
    )
    cross_workspace_response = owner_client.patch(
        f"/api/v1/workspaces/{outsider_workspace['id']}/accounts/{account['id']}",
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


def test_account_not_found_is_scoped_to_workspace(accounts_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    another_client = _sign_up_and_sign_in(accounts_client, "another@example.com")
    workspace = _create_workspace(owner_client, name="Casa", workspace_type="personal")
    other_workspace = _create_workspace(another_client, name="Otro", workspace_type="personal")
    account = _create_account(
        another_client,
        workspace_id=other_workspace["id"],
        name="Cuenta Externa",
        account_type="bank_account",
        currency="USD",
        initial_balance_minor=400,
        description=None,
    )

    response = owner_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}",
        json={"name": "No existe"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found."}


def test_archived_account_cannot_be_updated(accounts_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(accounts_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Historial", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=300,
        description=None,
    )
    archive_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}/archive"
    )
    assert archive_response.status_code == 200

    update_response = owner_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}",
        json={"name": "Caja nueva"},
    )

    assert update_response.status_code == 409
    assert update_response.json() == {"detail": "Archived accounts cannot be updated."}


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


def _create_account(
    client: TestClient,
    *,
    workspace_id: str,
    name: str,
    account_type: str,
    currency: str,
    initial_balance_minor: int,
    description: str | None,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/accounts",
        json={
            "name": name,
            "type": account_type,
            "currency": currency,
            "initial_balance_minor": initial_balance_minor,
            "description": description,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())
