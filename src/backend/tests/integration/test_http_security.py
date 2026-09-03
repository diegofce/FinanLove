from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.infrastructure.database import get_db
from app.main import app


async def fake_db() -> AsyncIterator[object]:
    yield object()


@pytest.mark.asyncio
async def test_refresh_rejects_missing_csrf_origin_over_http() -> None:
    app.dependency_overrides[get_db] = fake_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh", cookies={"refresh_token": "opaque"}
            )
        assert response.status_code == 403
        assert response.json()["detail"] == "CSRF validation failed"
    finally:
        app.dependency_overrides.pop(get_db, None)
