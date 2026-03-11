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
def transactions_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "transactions.db"
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


def test_member_can_create_list_get_update_and_delete_income_transaction(
    transactions_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
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

    destination_account = _create_account(
        member_client,
        workspace_id=workspace["id"],
        name="Cuenta sueldo",
        account_type="bank_account",
        currency="ars",
        initial_balance_minor=100000,
        description=None,
    )
    income_category = _find_category_by_name(
        member_client,
        workspace_id=workspace["id"],
        name="Salario",
    )

    create_response = member_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "income",
            "destination_account_id": destination_account["id"],
            "category_id": income_category["id"],
            "paid_by_user_id": member_client.get("/api/v1/auth/me").json()["user"]["id"],
            "amount_minor": 50000,
            "currency": "ars",
            "description": "Sueldo marzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {"kind": "solo"},
        },
    )
    assert create_response.status_code == 201
    transaction = create_response.json()
    assert transaction["type"] == "income"
    assert transaction["source_account_id"] is None
    assert transaction["destination_account_id"] == destination_account["id"]
    assert transaction["category_id"] == income_category["id"]
    assert transaction["currency"] == "ARS"
    assert transaction["source_account"] is None
    assert transaction["destination_account"]["id"] == destination_account["id"]
    assert transaction["category"]["name"] == "Salario"
    assert transaction["paid_by_user"]["email"] == "member@example.com"
    assert transaction["split_config"] == {"kind": "solo"}

    detail_response = member_client.get(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )
    list_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/transactions")

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == transaction["id"]
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["transactions"]] == [transaction["id"]]

    accounts_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")
    assert accounts_response.status_code == 200
    assert accounts_response.json()["accounts"][0]["current_balance_minor"] == 150000

    update_response = member_client.patch(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}",
        json={
            "amount_minor": 65000,
            "description": "Sueldo marzo actualizado",
            "occurred_at": "2026-03-10T15:30:00Z",
        },
    )
    assert update_response.status_code == 200
    updated_transaction = update_response.json()
    assert updated_transaction["amount_minor"] == 65000
    assert updated_transaction["description"] == "Sueldo marzo actualizado"
    assert updated_transaction["occurred_at"] == "2026-03-10T15:30:00Z"

    accounts_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")
    assert accounts_response.json()["accounts"][0]["current_balance_minor"] == 165000

    delete_response = member_client.delete(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )
    assert delete_response.status_code == 204

    deleted_detail_response = member_client.get(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )
    accounts_response = member_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")
    assert deleted_detail_response.status_code == 404
    assert deleted_detail_response.json() == {"detail": "Transaction not found."}
    assert accounts_response.json()["accounts"][0]["current_balance_minor"] == 100000


def test_transfer_updates_both_accounts_and_requires_same_currency(
    transactions_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Transferencias", workspace_type="personal")
    source_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=20000,
        description=None,
    )
    destination_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Banco",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=5000,
        description=None,
    )
    foreign_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="USD",
        account_type="savings_account",
        currency="USD",
        initial_balance_minor=1000,
        description=None,
    )

    create_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "transfer",
            "source_account_id": source_account["id"],
            "destination_account_id": destination_account["id"],
            "amount_minor": 3500,
            "currency": "ARS",
            "description": "Pasaje a cuenta",
            "occurred_at": "2026-03-10T10:00:00Z",
            "split_config": None,
        },
    )
    assert create_response.status_code == 201
    transaction = create_response.json()
    assert transaction["category_id"] is None
    assert transaction["source_account"]["id"] == source_account["id"]
    assert transaction["destination_account"]["id"] == destination_account["id"]

    accounts_response = owner_client.get(f"/api/v1/workspaces/{workspace['id']}/accounts")
    balances = {
        account["id"]: account["current_balance_minor"]
        for account in accounts_response.json()["accounts"]
    }
    assert balances[source_account["id"]] == 16500
    assert balances[destination_account["id"]] == 8500

    invalid_transfer_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "transfer",
            "source_account_id": source_account["id"],
            "destination_account_id": foreign_account["id"],
            "amount_minor": 100,
            "currency": "ARS",
            "description": None,
            "occurred_at": "2026-03-10T10:00:00Z",
            "split_config": None,
        },
    )
    assert invalid_transfer_response.status_code == 422
    assert invalid_transfer_response.json() == {
        "detail": "Transaction currency must match the linked account currency."
    }

    same_account_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "transfer",
            "source_account_id": source_account["id"],
            "destination_account_id": source_account["id"],
            "amount_minor": 100,
            "currency": "ARS",
            "description": None,
            "occurred_at": "2026-03-10T10:00:00Z",
            "split_config": None,
        },
    )
    assert same_account_response.status_code == 422
    assert same_account_response.json() == {
        "detail": "Transfer transactions require different source and destination accounts."
    }


def test_expense_validation_enforces_workspace_resources_and_archived_state(
    transactions_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    outsider_client = _sign_up_and_sign_in(transactions_client, "outsider@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="personal")
    outsider_workspace = _create_workspace(
        outsider_client,
        name="Ajeno",
        workspace_type="personal",
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Tarjeta",
        account_type="credit_card",
        currency="ARS",
        initial_balance_minor=0,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )
    income_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Salario",
    )
    outsider_account = _create_account(
        outsider_client,
        workspace_id=outsider_workspace["id"],
        name="Cuenta externa",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=0,
        description=None,
    )

    wrong_category_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": income_category["id"],
            "amount_minor": 2500,
            "currency": "ARS",
            "description": "Error",
            "occurred_at": "2026-03-10T08:00:00Z",
        },
    )
    assert wrong_category_response.status_code == 422
    assert wrong_category_response.json() == {
        "detail": "Expense transactions require an expense category."
    }

    cross_workspace_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": outsider_account["id"],
            "category_id": expense_category["id"],
            "amount_minor": 2500,
            "currency": "ARS",
            "description": "Error",
            "occurred_at": "2026-03-10T08:00:00Z",
        },
    )
    assert cross_workspace_response.status_code == 404
    assert cross_workspace_response.json() == {
        "detail": "source_account_id references an account that was not found in this workspace."
    }

    archive_account_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/accounts/{account['id']}/archive"
    )
    assert archive_account_response.status_code == 200

    archived_account_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": expense_category["id"],
            "amount_minor": 2500,
            "currency": "ARS",
            "description": "Error",
            "occurred_at": "2026-03-10T08:00:00Z",
        },
    )
    assert archived_account_response.status_code == 409
    assert archived_account_response.json() == {
        "detail": "source_account_id references an archived account."
    }


def test_transaction_access_is_scoped_to_workspace_membership(
    transactions_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    outsider_client = _sign_up_and_sign_in(transactions_client, "outsider@example.com")
    workspace = _create_workspace(owner_client, name="Privado", workspace_type="shared")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=1000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Salario")
    transaction = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "income",
            "destination_account_id": account["id"],
            "category_id": category["id"],
            "amount_minor": 100,
            "currency": "ARS",
            "description": None,
            "occurred_at": "2026-03-10T10:00:00Z",
        },
    ).json()

    list_response = outsider_client.get(f"/api/v1/workspaces/{workspace['id']}/transactions")
    detail_response = outsider_client.get(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )
    delete_response = outsider_client.delete(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )

    assert list_response.status_code == 403
    assert list_response.json() == {"detail": "You do not have access to this workspace."}
    assert detail_response.status_code == 403
    assert detail_response.json() == {"detail": "You do not have access to this workspace."}
    assert delete_response.status_code == 403
    assert delete_response.json() == {"detail": "You do not have access to this workspace."}


def test_transaction_not_found_is_scoped_to_workspace(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    another_client = _sign_up_and_sign_in(transactions_client, "another@example.com")
    workspace = _create_workspace(owner_client, name="Principal", workspace_type="personal")
    other_workspace = _create_workspace(another_client, name="Otra", workspace_type="personal")
    account = _create_account(
        another_client,
        workspace_id=other_workspace["id"],
        name="Cuenta externa",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=500,
        description=None,
    )
    category = _find_category_by_name(
        another_client, workspace_id=other_workspace["id"], name="Salario"
    )
    transaction = another_client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/transactions",
        json={
            "type": "income",
            "destination_account_id": account["id"],
            "category_id": category["id"],
            "amount_minor": 100,
            "currency": "ARS",
            "description": None,
            "occurred_at": "2026-03-10T10:00:00Z",
        },
    ).json()

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found."}


def test_occurred_at_must_be_timezone_aware(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Fechas", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=1000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Salario")

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "income",
            "destination_account_id": account["id"],
            "category_id": category["id"],
            "amount_minor": 100,
            "currency": "ARS",
            "description": None,
            "occurred_at": "2026-03-10T10:00:00",
        },
    )

    assert response.status_code == 422
    assert "occurred_at must be timezone-aware" in response.json()["detail"][0]["msg"]


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
    return response.json()


def _create_invitation(client: TestClient, *, workspace_id: str, email: str) -> dict[str, str]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": email},
    )
    assert response.status_code == 201
    return response.json()


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
    return response.json()


def _find_category_by_name(
    client: TestClient, *, workspace_id: str, name: str
) -> dict[str, object]:
    response = client.get(f"/api/v1/workspaces/{workspace_id}/categories")
    assert response.status_code == 200
    for category in response.json()["categories"]:
        if category["name"] == name:
            return category
    raise AssertionError(f"Category {name!r} not found")
