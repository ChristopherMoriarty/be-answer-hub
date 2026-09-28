from typing import Annotated

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """JSON login payload. The OAuth2 form uses username for the same email."""

    email: EmailStr
    password: Annotated[str, Field(min_length=1)]


class RefreshRequest(BaseModel):
    """Exchange a refresh token for a new access and refresh pair."""

    refresh_token: Annotated[str, Field(min_length=1)]


class UserCreate(schemas.BaseUserCreate):
    """Payload for inserting an account. There is no public registration route."""
