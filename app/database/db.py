from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings


class Database:
    """Database connection manager."""

    def __init__(self, url: str) -> None:
        self.__engine: AsyncEngine = create_async_engine(
            url=url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            echo=False,
            pool_pre_ping=True,
        )
        self.__session_factory = sessionmaker(  # type:ignore[call-overload]
            bind=self.__engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide an asynchronous context manager for an SQLAlchemy session."""
        session = self.__session_factory()
        try:
            yield session
        except (SQLAlchemyError, DBAPIError):
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """Release all resources associated with the database engine."""
        await self.__engine.dispose()
