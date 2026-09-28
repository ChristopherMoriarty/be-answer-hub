import uuid

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Public user fields."""


class TokenResponse(BaseModel):
    """Access token plus a rotatable refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
