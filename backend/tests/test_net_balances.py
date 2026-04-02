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
def net_balances_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    database_path = tmp_path / "net_balances.db"
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


def _accept_invitation(client: TestClient, *, invitation: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/workspaces/invitations/accept",
        json={"token": invitation["invitation_token"]},
    )
    assert response.status_code == 200


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


def _get_user_id(client: TestClient) -> str:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    return cast(str, response.json()["user"]["id"])


def _create_expense(
    client: TestClient,
    *,
    workspace_id: str,
    source_account_id: str,
    category_id: str,
    paid_by_user_id: str,
    amount_minor: int,
    currency: str,
    description: str,
    split_config: dict[str, object] | None = None,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/transactions",
        json={
            "type": "expense",
            "source_account_id": source_account_id,
            "category_id": category_id,
            "paid_by_user_id": paid_by_user_id,
            "amount_minor": amount_minor,
            "currency": currency.lower(),
            "description": description,
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": split_config,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def _create_transfer(
    client: TestClient,
    *,
    workspace_id: str,
    source_account_id: str,
    destination_account_id: str,
    amount_minor: int,
    currency: str,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/transactions",
        json={
            "type": "transfer",
            "source_account_id": source_account_id,
            "destination_account_id": destination_account_id,
            "amount_minor": amount_minor,
            "currency": currency,
            "description": "Transfer test",
            "occurred_at": "2026-03-10T12:00:00Z",
            "split_config": None,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def _create_shared_workspace(
    owner_client: TestClient,
    member_client: TestClient,
    *,
    workspace_name: str = "Casa",
) -> dict[str, str]:
    workspace = _create_workspace(owner_client, name=workspace_name, workspace_type="shared")
    member_email = member_client.get("/api/v1/auth/me").json()["user"]["email"]
    invitation = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email=member_email,
    )
    _accept_invitation(member_client, invitation=invitation)
    return workspace


def _create_shared_workspace_with_three_members(
    owner_client: TestClient,
    member_a_client: TestClient,
    member_b_client: TestClient,
) -> dict[str, str]:
    workspace = _create_workspace(owner_client, name="Tres", workspace_type="shared")

    member_a_email = member_a_client.get("/api/v1/auth/me").json()["user"]["email"]
    invitation_a = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email=member_a_email,
    )
    _accept_invitation(member_a_client, invitation=invitation_a)

    member_b_email = member_b_client.get("/api/v1/auth/me").json()["user"]["email"]
    invitation_b = _create_invitation(
        owner_client,
        workspace_id=workspace["id"],
        email=member_b_email,
    )
    _accept_invitation(member_b_client, invitation=invitation_b)

    return workspace


def test_equal_split_produces_correct_net_balance(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner@example.com")
    member_client = _sign_up_and_sign_in(net_balances_client, "member@example.com")
    workspace = _create_shared_workspace(owner_client, member_client)

    owner_id = _get_user_id(owner_client)
    member_id = _get_user_id(member_client)

    owner_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta owner",
        account_type="bank_account",
        currency="ars",
        initial_balance_minor=100000,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, owner_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=10000,
        currency="ars",
        description="Cena compartida",
        split_config={
            "type": "equal",
            "values": {owner_id: 1, member_id: 1},
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["balances"]) == 1
    entry = data["balances"][0]
    assert entry["debtor_id"] == member_id
    assert entry["creditor_id"] == owner_id
    assert entry["amount_minor"] == 5000
    assert entry["currency"] == "ARS"
    assert entry["debtor"]["email"] == "member@example.com"
    assert entry["creditor"]["email"] == "owner@example.com"


def test_percentage_split_produces_correct_net_balance(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_pct@example.com")
    member_client = _sign_up_and_sign_in(net_balances_client, "member_pct@example.com")
    workspace = _create_shared_workspace(owner_client, member_client)

    owner_id = _get_user_id(owner_client)
    member_id = _get_user_id(member_client)

    owner_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta owner",
        account_type="bank_account",
        currency="ars",
        initial_balance_minor=100000,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, owner_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=10000,
        currency="ars",
        description="Cena por porcentaje",
        split_config={
            "type": "percentage",
            "values": {owner_id: 70, member_id: 30},
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["balances"]) == 1
    entry = data["balances"][0]
    assert entry["debtor_id"] == member_id
    assert entry["creditor_id"] == owner_id
    assert entry["amount_minor"] == 3000
    assert entry["currency"] == "ARS"


def test_multiple_transactions_net_correctly(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_multi@example.com")
    member_client = _sign_up_and_sign_in(net_balances_client, "member_multi@example.com")
    workspace = _create_shared_workspace(owner_client, member_client)

    owner_id = _get_user_id(owner_client)
    member_id = _get_user_id(member_client)

    owner_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta owner",
        account_type="bank_account",
        currency="ars",
        initial_balance_minor=100000,
        description=None,
    )
    member_account = _create_account(
        member_client,
        workspace_id=workspace["id"],
        name="Cuenta member",
        account_type="bank_account",
        currency="ars",
        initial_balance_minor=100000,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    # Owner pays 10000, equal split -> member owes owner 5000
    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, owner_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=10000,
        currency="ars",
        description="Cena",
        split_config={
            "type": "equal",
            "values": {owner_id: 1, member_id: 1},
        },
    )

    # Member pays 6000, equal split -> owner owes member 3000
    _create_expense(
        member_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, member_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=member_id,
        amount_minor=6000,
        currency="ars",
        description="Almuerzo",
        split_config={
            "type": "equal",
            "values": {owner_id: 1, member_id: 1},
        },
    )

    # Net: member owes owner 5000 - 3000 = 2000
    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["balances"]) == 1
    entry = data["balances"][0]
    assert entry["debtor_id"] == member_id
    assert entry["creditor_id"] == owner_id
    assert entry["amount_minor"] == 2000
    assert entry["currency"] == "ARS"


def test_transfers_excluded_from_net_balance(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_transfer@example.com")
    workspace = _create_workspace(owner_client, name="TransferTest", workspace_type="personal")

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

    _create_transfer(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, source_account["id"]),
        destination_account_id=cast(str, destination_account["id"]),
        amount_minor=3500,
        currency="ARS",
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balances"] == []


def test_solo_transactions_excluded_from_net_balance(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_solo@example.com")
    workspace = _create_workspace(owner_client, name="SoloTest", workspace_type="personal")

    owner_id = _get_user_id(owner_client)

    account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Banco",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=100000,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=5000,
        currency="ars",
        description="Almuerzo personal",
        split_config=None,
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balances"] == []


def test_multi_currency_produces_separate_balances(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_currency@example.com")
    member_client = _sign_up_and_sign_in(net_balances_client, "member_currency@example.com")
    workspace = _create_shared_workspace(owner_client, member_client)

    owner_id = _get_user_id(owner_client)
    member_id = _get_user_id(member_client)

    ars_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta ARS",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=100000,
        description=None,
    )
    usd_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta USD",
        account_type="bank_account",
        currency="USD",
        initial_balance_minor=100000,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, ars_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=10000,
        currency="ars",
        description="Cena ARS",
        split_config={
            "type": "equal",
            "values": {owner_id: 1, member_id: 1},
        },
    )

    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, usd_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=2000,
        currency="usd",
        description="Cena USD",
        split_config={
            "type": "equal",
            "values": {owner_id: 1, member_id: 1},
        },
    )

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["balances"]) == 2

    currencies = {entry["currency"] for entry in data["balances"]}
    assert currencies == {"ARS", "USD"}

    for entry in data["balances"]:
        assert entry["debtor_id"] == member_id
        assert entry["creditor_id"] == owner_id
        if entry["currency"] == "ARS":
            assert entry["amount_minor"] == 5000
        elif entry["currency"] == "USD":
            assert entry["amount_minor"] == 1000


def test_user_id_filter_returns_only_relevant_entries(
    net_balances_client: TestClient,
) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_filter@example.com")
    member_a_client = _sign_up_and_sign_in(net_balances_client, "member_a@example.com")
    member_b_client = _sign_up_and_sign_in(net_balances_client, "member_b@example.com")

    workspace = _create_shared_workspace_with_three_members(
        owner_client,
        member_a_client,
        member_b_client,
    )

    owner_id = _get_user_id(owner_client)
    member_a_id = _get_user_id(member_a_client)
    member_b_id = _get_user_id(member_b_client)

    owner_account = _create_account(
        owner_client,
        workspace_id=workspace["id"],
        name="Cuenta owner",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=100000,
        description=None,
    )
    member_a_account = _create_account(
        member_a_client,
        workspace_id=workspace["id"],
        name="Cuenta member A",
        account_type="bank_account",
        currency="ARS",
        initial_balance_minor=100000,
        description=None,
    )
    expense_category = _find_category_by_name(
        owner_client,
        workspace_id=workspace["id"],
        name="Comida",
    )

    # Owner pays 10000, split owner/member_a -> member_a owes owner 5000
    _create_expense(
        owner_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, owner_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=owner_id,
        amount_minor=10000,
        currency="ars",
        description="Cena owner/member_a",
        split_config={
            "type": "equal",
            "values": {owner_id: 1, member_a_id: 1},
        },
    )

    # Member A pays 4000, split member_a/member_b -> member_b owes member_a 2000
    _create_expense(
        member_a_client,
        workspace_id=workspace["id"],
        source_account_id=cast(str, member_a_account["id"]),
        category_id=cast(str, expense_category["id"]),
        paid_by_user_id=member_a_id,
        amount_minor=4000,
        currency="ars",
        description="Almuerzo member_a/member_b",
        split_config={
            "type": "equal",
            "values": {member_a_id: 1, member_b_id: 1},
        },
    )

    # Filter by member_a: should return both entries (member_a is debtor in one, creditor in other)
    response = member_a_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
        params={"user_id": member_a_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["balances"]) == 2

    # Filter by owner: should return only the owner/member_a entry
    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
        params={"user_id": owner_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["balances"]) == 1
    assert data["balances"][0]["debtor_id"] == member_a_id
    assert data["balances"][0]["creditor_id"] == owner_id
    assert data["balances"][0]["amount_minor"] == 5000


def test_non_member_gets_403(net_balances_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_authz@example.com")
    outsider_client = _sign_up_and_sign_in(net_balances_client, "outsider_authz@example.com")
    workspace = _create_workspace(owner_client, name="Privado", workspace_type="shared")

    response = outsider_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have access to this workspace."}


def test_empty_workspace_returns_empty_list(net_balances_client: TestClient) -> None:
    owner_client = _sign_up_and_sign_in(net_balances_client, "owner_empty@example.com")
    workspace = _create_workspace(owner_client, name="Vacio", workspace_type="personal")

    response = owner_client.get(
        f"/api/v1/workspaces/{workspace['id']}/net-balances",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balances"] == []
