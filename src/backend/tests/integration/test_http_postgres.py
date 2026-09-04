from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient


async def register_and_login(client: AsyncClient) -> str:
    suffix = uuid4().hex[:12]
    payload = {
        "username": f"http_{suffix}",
        "email": f"{suffix}@example.com",
        "first_name": "HTTP",
        "last_name": "Tester",
        "password": "A-very-secure-password-123",
    }
    registered = await client.post("/api/v1/auth/register", json=payload)
    assert registered.status_code == 201
    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"login": payload["username"], "password": payload["password"]},
    )
    assert logged_in.status_code == 200
    return str(logged_in.json()["access_token"])


@pytest.mark.asyncio
async def test_auth_http_flow_rotation_reuse_logout_and_me(
    http_client: AsyncClient,
) -> None:
    access_token = await register_and_login(http_client)
    headers = {"Authorization": f"Bearer {access_token}"}
    me = await http_client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"].startswith("http_")

    first_refresh = http_client.cookies.get("refresh_token")
    assert first_refresh is not None
    rotated = await http_client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )
    assert rotated.status_code == 200
    replacement = http_client.cookies.get("refresh_token")
    assert replacement is not None and replacement != first_refresh

    reused = await http_client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": f"refresh_token={first_refresh}",
        },
    )
    assert reused.status_code == 401

    logged_out = await http_client.post("/api/v1/auth/logout")
    assert logged_out.status_code == 204
    assert http_client.cookies.get("refresh_token") is None


@pytest.mark.asyncio
async def test_transaction_idempotency_and_payload_conflict(
    http_client: AsyncClient,
) -> None:
    token = await register_and_login(http_client)
    headers = {"Authorization": f"Bearer {token}"}
    account = await http_client.post(
        "/api/v1/accounts",
        headers=headers,
        json={
            "name": f"Idempotent {uuid4().hex[:8]}",
            "account_type": "BANK",
            "currency": "COP",
            "current_balance": "100.00",
        },
    )
    assert account.status_code == 201
    account_id = account.json()["id"]
    payload: dict[str, Any] = {
        "account_id": account_id,
        "transaction_type": "EXPENSE",
        "amount": "20.00",
        "description": "same request",
    }
    first = await http_client.post(
        "/api/v1/transactions",
        headers={**headers, "Idempotency-Key": "request-1"},
        json=payload,
    )
    second = await http_client.post(
        "/api/v1/transactions",
        headers={**headers, "Idempotency-Key": "request-1"},
        json=payload,
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    conflict = await http_client.post(
        "/api/v1/transactions",
        headers={**headers, "Idempotency-Key": "request-1"},
        json={**payload, "description": "different payload"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "Idempotency key payload conflict"


@pytest.mark.asyncio
async def test_account_and_recurring_transaction_ownership(
    http_client: AsyncClient,
) -> None:
    owner_token = await register_and_login(http_client)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    account = await http_client.post(
        "/api/v1/accounts",
        headers=owner_headers,
        json={"name": "Owned", "account_type": "BANK",
              "current_balance": "100.00"},
    )
    assert account.status_code == 201
    account_id = account.json()["id"]

    other_token = await register_and_login(http_client)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    accounts = await http_client.get("/api/v1/accounts", headers=other_headers)
    assert accounts.status_code == 200
    assert accounts.json() == []
    recurring = await http_client.post(
        "/api/v1/recurring-transactions",
        headers=other_headers,
        json={
            "account_id": account_id,
            "transaction_type": "EXPENSE",
            "amount": "10.00",
            "description": "not owned",
            "frequency": "MONTHLY",
            "next_run_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
    )
    assert recurring.status_code == 400
    assert "account" in recurring.json()["detail"].lower()
