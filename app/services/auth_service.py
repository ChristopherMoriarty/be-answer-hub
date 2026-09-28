import uuid
from dataclasses import dataclass
from typing import cast

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import JWTStrategy

from app.auth.users import UserManager
from app.core.settings import settings
from app.exceptions.auth import UnauthorizedServiceError
from app.models.user import User


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    """A freshly issued access and refresh pair."""

    access_token: str
    refresh_token: str
    expires_in: int


class _EmailPassword:
    """Minimal stand-in for the OAuth2 form FastAPI Users expects."""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password


class AuthService:
    """Login and refresh for accounts that already exist in the database."""

    def __init__(
        self,
        user_manager: UserManager,
        access_tokens: JWTStrategy[User, uuid.UUID],
        refresh_tokens: JWTStrategy[User, uuid.UUID],
    ) -> None:
        self._user_manager = user_manager
        self._access_tokens = access_tokens
        self._refresh_tokens = refresh_tokens

    async def login(self, email: str, password: str) -> IssuedTokens:
        """Check the password and issue an access and refresh pair."""
        credentials = cast(
            OAuth2PasswordRequestForm,
            _EmailPassword(email, password),
        )
        user = await self._user_manager.authenticate(credentials)
        if user is None or not user.is_active:
            raise UnauthorizedServiceError("Invalid credentials")
        return await self._issue_pair(user)

    async def refresh(self, raw_token: str) -> IssuedTokens:
        """Issue a new pair when the refresh JWT is still valid."""
        user = await self._refresh_tokens.read_token(raw_token, self._user_manager)
        if user is None or not user.is_active:
            raise UnauthorizedServiceError("Invalid refresh token")
        return await self._issue_pair(user)

    async def _issue_pair(self, user: User) -> IssuedTokens:
        return IssuedTokens(
            access_token=await self._access_tokens.write_token(user),
            refresh_token=await self._refresh_tokens.write_token(user),
            expires_in=settings.auth.access_ttl_seconds,
        )
