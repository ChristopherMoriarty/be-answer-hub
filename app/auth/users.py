import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import API_PREFIX
from app.core.settings import settings
from app.database.session import get_session
from app.models.user import User


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Authenticates accounts that already exist in the database."""

    reset_password_token_secret = settings.auth.jwt_secret
    verification_token_secret = settings.auth.jwt_secret


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID], None]:
    """Provide the FastAPI Users SQLAlchemy adapter."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Provide a user manager bound to the request session."""
    yield UserManager(user_db)


REFRESH_TOKEN_AUDIENCE = ["fastapi-users:refresh"]


def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    """Build the access-token strategy."""
    return JWTStrategy(
        secret=settings.auth.jwt_secret,
        lifetime_seconds=settings.auth.access_ttl_seconds,
    )


def get_refresh_strategy() -> JWTStrategy[User, uuid.UUID]:
    """Build the refresh-token strategy. A different audience keeps it off API routes."""
    return JWTStrategy(
        secret=settings.auth.jwt_secret,
        lifetime_seconds=settings.auth.refresh_ttl_seconds,
        token_audience=REFRESH_TOKEN_AUDIENCE,
    )


bearer_transport = BearerTransport(tokenUrl=f"{API_PREFIX}/auth/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
