import asyncio
import os
from collections.abc import AsyncGenerator, Generator

from unittest.mock import AsyncMock, MagicMock, patch

# Tests must never touch the dev database — conftest truncates tables after each test.
os.environ["DATABASE__NAME"] = os.getenv("TEST_DATABASE__NAME", "answer_hub_test")
os.environ.setdefault("AUTH__JWT_SECRET", "test-jwt-secret-not-for-production")
os.environ.setdefault("AUTH__ACCESS_TTL_SECONDS", "900")
os.environ.setdefault("AUTH__REFRESH_TTL_SECONDS", "604800")
if os.getenv("DATABASE__HOST", "postgres") == "postgres" and not os.path.exists(
    "/.dockerenv"
):
    os.environ["DATABASE__HOST"] = "localhost"

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.core.settings import settings
from app.database.session import db
from app.main import app
from app.models.user import User
from tests.factories import FACTORIES

TEST_DATABASE_NAME = os.environ["DATABASE__NAME"]


@pytest.fixture(scope="session", autouse=True)
def mock_minio_client() -> MagicMock:
    """Avoid real MinIO connections during tests."""
    mock = MagicMock()
    mock.ensure_bucket = AsyncMock()
    mock.put_object = AsyncMock()
    mock.delete_object = AsyncMock()
    mock.presigned_get_url = AsyncMock(return_value="https://example.com/cv/test.pdf")
    mock.get_object = AsyncMock(return_value=b"%PDF-1.4 preview")

    with patch("app.main.MinioClient", return_value=mock):
        app.state.minio_client = mock
        yield mock


@pytest.fixture(autouse=True)
def reset_minio_mock(mock_minio_client: MagicMock) -> None:
    """Reset MinIO mock call history between tests."""
    mock_minio_client.reset_mock()
    mock_minio_client.ensure_bucket = AsyncMock()
    mock_minio_client.put_object = AsyncMock()
    mock_minio_client.delete_object = AsyncMock()
    mock_minio_client.presigned_get_url = AsyncMock(
        return_value="https://example.com/cv/test.pdf"
    )
    mock_minio_client.get_object = AsyncMock(return_value=b"%PDF-1.4 preview")


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def _authenticated_user() -> User:
    """Stand-in user so existing API tests skip the login flow."""
    return User(
        email="test@example.com",
        hashed_password="not-used",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )


@pytest.fixture
async def client():
    """HTTP client with authentication bypassed."""
    app.dependency_overrides[current_active_user] = _authenticated_user
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(current_active_user, None)


@pytest.fixture
async def anon_client():
    """HTTP client without an access token."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Shared database session wired to factory-boy factories."""
    async with db.get_session() as session:
        for factory_ in FACTORIES:
            factory_._meta.sqlalchemy_session = session  # type: ignore[attr-defined]
        yield session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_db(async_db_session: AsyncSession) -> AsyncGenerator[None, None]:
    """Clear test data after each test."""
    if settings.database.name != TEST_DATABASE_NAME:
        raise RuntimeError(
            f"Refusing to truncate database {settings.database.name!r}. "
            f"Tests must use {TEST_DATABASE_NAME!r}."
        )

    yield

    await async_db_session.execute(
        text("TRUNCATE TABLE users, cv, nodes, hiring_board RESTART IDENTITY CASCADE")
    )
    await async_db_session.commit()
