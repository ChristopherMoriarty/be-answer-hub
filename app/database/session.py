from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.database.db import Database

db = Database(url=settings.database.url)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for FastAPI to get database session."""
    async with db.get_session() as session:
        yield session
