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
from app.api.dependencies.transactions import _TEST_OBJECT_STORAGE
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
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://localhost:9000")
    monkeypatch.setenv("S3_REGION", "us-east-1")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "minioadmin")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("S3_BUCKET", "transaction-receipts-test")
    monkeypatch.setenv("S3_USE_SSL", "false")
    monkeypatch.setenv("S3_FORCE_PATH_STYLE", "true")
    monkeypatch.setenv("TRANSACTION_RECEIPT_MAX_SIZE_BYTES", str(10 * 1024 * 1024))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("WORKSPACE_INVITATION_TTL_SECONDS", "3600")

    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    _TEST_REDIS._values.clear()
    _TEST_OBJECT_STORAGE.clear()

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
            "split_config": None,
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
    assert transaction["split_config"] is None

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


def test_member_can_upload_and_fetch_transaction_receipt(
    transactions_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Recibos", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Banco",
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
            "description": "Con recibo",
            "occurred_at": "2026-03-10T10:00:00Z",
        },
    ).json()

    upload_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}/receipt",
        files={"receipt": ("ticket.png", b"png-bytes", "image/png")},
    )

    assert upload_response.status_code == 201
    receipt_url = upload_response.json()["receipt_url"]
    assert (
        receipt_url == "/api/v1/workspaces/"
        f"{workspace['id']}/transactions/{transaction['id']}/receipt/receipt.png"
    )

    transaction_detail_response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )
    assert transaction_detail_response.status_code == 200
    assert transaction_detail_response.json()["receipt_url"] == receipt_url

    receipt_response = owner_client.get(receipt_url)
    assert receipt_response.status_code == 200
    assert receipt_response.headers["content-type"] == "image/png"
    assert receipt_response.content == b"png-bytes"


def test_receipt_reupload_replaces_previous_object(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Recibos", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=1000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    transaction = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "amount_minor": 100,
            "currency": "ARS",
            "description": "Con recibo",
            "occurred_at": "2026-03-10T10:00:00Z",
        },
    ).json()

    first_upload_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}/receipt",
        files={"receipt": ("ticket.png", b"first", "image/png")},
    )
    assert first_upload_response.status_code == 201
    first_receipt_url = first_upload_response.json()["receipt_url"]

    second_upload_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}/receipt",
        files={"receipt": ("ticket.pdf", b"%PDF-1.7", "application/pdf")},
    )
    assert second_upload_response.status_code == 201
    second_receipt_url = second_upload_response.json()["receipt_url"]
    assert second_receipt_url != first_receipt_url
    assert second_receipt_url.endswith("receipt.pdf")

    old_receipt_response = owner_client.get(first_receipt_url)
    new_receipt_response = owner_client.get(second_receipt_url)
    transaction_detail_response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}"
    )

    assert old_receipt_response.status_code == 404
    assert old_receipt_response.json() == {"detail": "Receipt not found."}
    assert new_receipt_response.status_code == 200
    assert new_receipt_response.headers["content-type"] == "application/pdf"
    assert new_receipt_response.content == b"%PDF-1.7"
    assert transaction_detail_response.json()["receipt_url"] == second_receipt_url


def test_receipt_upload_rejects_invalid_media_type_and_size(
    transactions_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Recibos", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Banco",
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

    invalid_media_type_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}/receipt",
        files={"receipt": ("ticket.gif", b"gif", "image/gif")},
    )
    assert invalid_media_type_response.status_code == 422
    assert invalid_media_type_response.json() == {
        "detail": (
            "Unsupported receipt media type. Allowed types: image/png, image/jpeg, application/pdf."
        )
    }

    oversized_receipt_response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions/{transaction['id']}/receipt",
        files={
            "receipt": (
                "ticket.pdf",
                b"x" * (10 * 1024 * 1024 + 1),
                "application/pdf",
            )
        },
    )
    assert oversized_receipt_response.status_code == 413
    assert oversized_receipt_response.json() == {"detail": "Receipt exceeds the 10 MB size limit."}


def test_split_config_rejects_invalid_type(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "amount_minor": 5000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {"type": "invalid", "values": {}},
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "split_config.type" in detail or "type" in str(detail)


def test_split_config_requires_paid_by_user_id(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="personal")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "amount_minor": 5000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {"type": "equal"},
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "paid_by_user_id" in detail


def test_percentage_split_must_sum_to_100(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "percentage",
                "values": {owner_id: 60, member_id: 30},
            },
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "100" in detail or "sum" in detail.lower()


def test_percentage_split_values_must_be_0_to_100(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "percentage",
                "values": {owner_id: 50, member_id: 150},
            },
        },
    )
    assert response.status_code == 422


def test_exact_split_must_sum_to_amount(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "exact",
                "values": {owner_id: 6000, member_id: 3000},
            },
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "10000" in detail or "sum" in detail.lower()


def test_exact_split_values_must_be_positive(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "exact",
                "values": {owner_id: 0, member_id: 10000},
            },
        },
    )
    assert response.status_code == 422


def test_split_config_rejects_non_member_user(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    non_member_id = "00000000-0000-0000-0000-000000000001"

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "percentage",
                "values": {owner_id: 50, non_member_id: 50},
            },
        },
    )
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "member" in detail.lower() or "workspace" in detail.lower()


def test_valid_equal_split_accepted(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "equal",
                "values": {owner_id: 1, member_id: 1},
            },
        },
    )
    assert response.status_code == 201
    transaction = response.json()
    assert transaction["split_config"]["type"] == "equal"
    assert owner_id in transaction["split_config"]["values"]
    assert member_id in transaction["split_config"]["values"]


def test_valid_percentage_split_accepted(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "percentage",
                "values": {owner_id: 60, member_id: 40},
            },
        },
    )
    assert response.status_code == 201
    transaction = response.json()
    assert transaction["split_config"]["type"] == "percentage"


def test_valid_exact_split_accepted(transactions_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(transactions_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(transactions_client, "member@example.com")
    workspace = _create_workspace(owner_client, name="Gastos", workspace_type="shared")
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email="member@example.com",
    )
    member_client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Caja",
        account_type="cash",
        currency="ARS",
        initial_balance_minor=10000,
        description=None,
    )
    category = _find_category_by_name(owner_client, workspace_id=workspace["id"], name="Comida")
    owner_id = owner_client.get("/api/v1/auth/me").json()["user"]["id"]
    member_id = member_client.get("/api/v1/auth/me").json()["user"]["id"]

    response = owner_client.post(
        f"/api/v1/workspaces/{workspace['id']}/transactions",
        json={
            "type": "expense",
            "source_account_id": account["id"],
            "category_id": category["id"],
            "paid_by_user_id": owner_id,
            "amount_minor": 10000,
            "currency": "ARS",
            "description": "Almuerzo",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": {
                "type": "exact",
                "values": {owner_id: 6000, member_id: 4000},
            },
        },
    )
    assert response.status_code == 201
    transaction = response.json()
    assert transaction["split_config"]["type"] == "exact"


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


def _find_category_by_name(
    client: TestClient, *, workspace_id: str, name: str
) -> dict[str, object]:
    response = client.get(f"/api/v1/workspaces/{workspace_id}/categories")
    assert response.status_code == 200
    for category in response.json()["categories"]:
        if category["name"] == name:
            return cast(dict[str, object], category)
    raise AssertionError(f"Category {name!r} not found")
