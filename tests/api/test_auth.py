from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi_users.db import SQLAlchemyUserDatabase

from app.auth.users import REFRESH_TOKEN_AUDIENCE, UserManager
from app.core.settings import settings
from app.database.session import db
from app.models.user import User
from app.schemas.requests.auth import UserCreate

TEST_EMAIL = "user@example.com"
TEST_PASSWORD = "test-password"


@pytest.fixture
async def account():
    """Insert a user the way accounts arrive in the database, without registration."""
    async with db.get_session() as session:
        manager = UserManager(SQLAlchemyUserDatabase(session, User))
        await manager.create(
            UserCreate(
                email=TEST_EMAIL,
                password=TEST_PASSWORD,
                is_active=True,
                is_verified=True,
            )
        )
    return TEST_EMAIL, TEST_PASSWORD


async def _login(anon_client, account: tuple[str, str]) -> dict:
    email, password = account
    response = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_login_returns_token_pair(anon_client, account):
    """Stored credentials issue an access token and a refresh token."""
    body = await _login(anon_client, account)
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.auth.access_ttl_seconds
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(anon_client, account):
    """A wrong password is rejected without revealing which part failed."""
    email, _password = account
    response = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_accepts_oauth2_form(anon_client, account):
    """Swagger's password dialog posts form fields, not JSON."""
    email, password = account
    response = await anon_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_protected_route_requires_access_token(anon_client):
    """Business routes reject a missing bearer token."""
    response = await anon_client.get("/api/v1/nodes/tree")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_opens_protected_route(anon_client, account):
    """A fresh access token can read the node tree."""
    tokens = await _login(anon_client, account)
    response = await anon_client.get(
        "/api/v1/nodes/tree",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_refresh_issues_a_new_access_token(anon_client, account):
    """A refresh JWT yields a new pair that can call protected routes."""
    tokens = await _login(anon_client, account)
    refreshed = await anon_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    response = await anon_client.get(
        "/api/v1/nodes/tree",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_access_token_cannot_refresh(anon_client, account):
    """An access token is not accepted as a refresh token."""
    tokens = await _login(anon_client, account)
    response = await anon_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_open_protected_route(anon_client, account):
    """A refresh token is not an access token."""
    tokens = await _login(anon_client, account)
    response = await anon_client.get(
        "/api/v1/nodes/tree",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_expired_token(anon_client, account):
    """An expired refresh JWT is rejected."""
    tokens = await _login(anon_client, account)
    payload = jwt.decode(
        tokens["refresh_token"],
        settings.auth.jwt_secret,
        algorithms=["HS256"],
        audience=REFRESH_TOKEN_AUDIENCE,
    )
    payload["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired = jwt.encode(payload, settings.auth.jwt_secret, algorithm="HS256")

    response = await anon_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_stays_public(anon_client):
    """Health does not require a token."""
    response = await anon_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
