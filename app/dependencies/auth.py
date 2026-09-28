from collections.abc import AsyncGenerator

from fastapi import Depends, Request

from app.auth.users import (
    UserManager,
    get_jwt_strategy,
    get_refresh_strategy,
    get_user_manager,
)
from app.schemas.requests.auth import LoginRequest
from app.services.auth_service import AuthService


async def get_login_credentials(request: Request) -> LoginRequest:
    """Read login credentials from JSON or the OAuth2 password form."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        return LoginRequest.model_validate(await request.json())

    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    return LoginRequest.model_validate(
        {
            "email": username if isinstance(username, str) else "",
            "password": password if isinstance(password, str) else "",
        }
    )


async def get_auth_service(
    user_manager: UserManager = Depends(get_user_manager),
) -> AsyncGenerator[AuthService, None]:
    """Provide an AuthService for the request."""
    yield AuthService(user_manager, get_jwt_strategy(), get_refresh_strategy())
