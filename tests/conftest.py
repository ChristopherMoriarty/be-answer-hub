import asyncio
from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import db
from app.main import app
from tests.factories import FACTORIES


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """HTTP client for the FastAPI application."""
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
    """Clear node data after each test."""
    yield

    await async_db_session.execute(
        text("TRUNCATE TABLE nodes RESTART IDENTITY CASCADE")
    )
    await async_db_session.commit()
