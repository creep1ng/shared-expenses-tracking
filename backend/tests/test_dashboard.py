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
def dashboard_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "dashboard.db"
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


def test_dashboard_kpis_aggregate_single_currency_period(dashboard_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Casa", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta principal",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=100000,
        description=None,
    )
    income_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Salario",
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "income",
            "destination_account_id": account["id"],
            "category_id": income_category["id"],
            "amount_minor": 50000,
            "currency": "ARS",
            "occurred_at": "2026-03-10T12:00:00Z",
        },
    )
    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": expense_category["id"],
            "amount_minor": 15000,
            "currency": "ARS",
            "occurred_at": "2026-03-11T12:00:00Z",
        },
    )
    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "income",
            "destination_account_id": account["id"],
            "category_id": income_category["id"],
            "amount_minor": 20000,
            "currency": "ARS",
            "occurred_at": "2026-02-20T12:00:00Z",
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-02-01", "end_date": "2026-02-28"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "date_range": {
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "start_at": "2026-02-01T00:00:00Z",
            "end_at_exclusive": "2026-03-01T00:00:00Z",
        },
        "total_balance": {
            "kind": "total_balance",
            "status": "available",
            "amount_minor": 155000,
            "currency": "ARS",
        },
        "total_income": {
            "kind": "total_income",
            "status": "available",
            "amount_minor": 20000,
            "currency": "ARS",
        },
        "total_expenses": {
            "kind": "total_expenses",
            "status": "available",
            "amount_minor": 0,
            "currency": "ARS",
        },
        "net_cash_flow": {
            "kind": "net_cash_flow",
            "status": "available",
            "amount_minor": 20000,
            "currency": "ARS",
        },
    }


def test_dashboard_kpis_exclude_transfers_from_period_analytics(
    dashboard_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Transferencias", workspace_type="personal")
    source_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=25000,
        description=None,
    )
    destination_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Banco",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )

    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "transfer",
            "source_account_id": source_account["id"],
            "destination_account_id": destination_account["id"],
            "amount_minor": 7000,
            "currency": "ARS",
            "occurred_at": "2026-03-10T12:00:00Z",
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-03-01", "end_date": "2026-03-31"},
    )

    assert response.status_code == 200
    assert response.json()["total_balance"] == {
        "kind": "total_balance",
        "status": "available",
        "amount_minor": 35000,
        "currency": "ARS",
    }
    assert response.json()["total_income"] == {
        "kind": "total_income",
        "status": "no_data",
    }
    assert response.json()["total_expenses"] == {
        "kind": "total_expenses",
        "status": "no_data",
    }
    assert response.json()["net_cash_flow"] == {
        "kind": "net_cash_flow",
        "status": "no_data",
    }


def test_dashboard_kpis_return_no_data_when_workspace_has_no_active_accounts_or_analytics(
    dashboard_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Vacio", workspace_type="personal")

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-03-01", "end_date": "2026-03-31"},
    )

    assert response.status_code == 200
    assert response.json()["total_balance"] == {
        "kind": "total_balance",
        "status": "no_data",
    }
    assert response.json()["total_income"] == {
        "kind": "total_income",
        "status": "no_data",
    }
    assert response.json()["total_expenses"] == {
        "kind": "total_expenses",
        "status": "no_data",
    }
    assert response.json()["net_cash_flow"] == {
        "kind": "net_cash_flow",
        "status": "no_data",
    }


def test_dashboard_kpis_return_mixed_currency_states(dashboard_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Mixto", workspace_type="personal")
    ars_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="ARS",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    usd_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="USD",
        account_type="savings_account",
        currency="USD",
        initial_balance_minor=5000,
        description=None,
    )
    income_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Salario",
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "income",
            "destination_account_id": ars_account["id"],
            "category_id": income_category["id"],
            "amount_minor": 1000,
            "currency": "ARS",
            "occurred_at": "2026-03-10T12:00:00Z",
        },
    )
    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "expense",
            "source_account_id": usd_account["id"],
            "category_id": expense_category["id"],
            "amount_minor": 500,
            "currency": "USD",
            "occurred_at": "2026-03-11T12:00:00Z",
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-03-01", "end_date": "2026-03-31"},
    )

    assert response.status_code == 200
    assert response.json()["total_balance"] == {
        "kind": "total_balance",
        "status": "mixed_currency",
    }
    assert response.json()["total_income"] == {
        "kind": "total_income",
        "status": "mixed_currency",
    }
    assert response.json()["total_expenses"] == {
        "kind": "total_expenses",
        "status": "mixed_currency",
    }
    assert response.json()["net_cash_flow"] == {
        "kind": "net_cash_flow",
        "status": "mixed_currency",
    }


def test_dashboard_kpis_require_workspace_access(dashboard_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    outsider_client = _sign_up_and_sign_in(dashboard_client, "outsider@example.com")
    workspace = _create_workspace(owner_client, name="Privado", workspace_type="personal")

    response = outsider_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-03-01", "end_date": "2026-03-31"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have access to this workspace."}


def test_dashboard_kpis_filter_by_normalized_date_range(dashboard_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Rango", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=0,
        description=None,
    )
    income_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Salario",
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "income",
            "destination_account_id": account["id"],
            "category_id": income_category["id"],
            "amount_minor": 1000,
            "currency": "ARS",
            "occurred_at": "2026-02-01T00:00:00Z",
        },
    )
    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": expense_category["id"],
            "amount_minor": 300,
            "currency": "ARS",
            "occurred_at": "2026-02-28T23:59:59Z",
        },
    )
    _create_transaction(
        owner_client,
        workspace_id=workspace["id"],
        payload={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": expense_category["id"],
            "amount_minor": 900,
            "currency": "ARS",
            "occurred_at": "2026-03-01T00:00:00Z",
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-02-01", "end_date": "2026-02-28"},
    )

    assert response.status_code == 200
    assert response.json()["total_income"] == {
        "kind": "total_income",
        "status": "available",
        "amount_minor": 1000,
        "currency": "ARS",
    }
    assert response.json()["total_expenses"] == {
        "kind": "total_expenses",
        "status": "available",
        "amount_minor": 300,
        "currency": "ARS",
    }
    assert response.json()["net_cash_flow"] == {
        "kind": "net_cash_flow",
        "status": "available",
        "amount_minor": 700,
        "currency": "ARS",
    }


def test_dashboard_kpis_validate_date_range(dashboard_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(dashboard_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Fechas", workspace_type="personal")

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/dashboard/kpis",
        params={"start_date": "2026-04-01", "end_date": "2026-03-31"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "start_date must be less than or equal to end_date."}


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


def _create_transaction(
    client: TestClient,
    *,
    workspace_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/transactions",
        json=payload,
    )
    assert response.status_code == 201
    return response.json()
