from fastapi import APIRouter, Depends

from app.core.constants import API_PREFIX
from app.dependencies.auth import get_auth_service, get_login_credentials
from app.schemas.requests.auth import LoginRequest, RefreshRequest
from app.schemas.responses.auth import TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix=f"{API_PREFIX}/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest = Depends(get_login_credentials),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Issue an access token and a refresh token."""
    tokens = await service.login(str(credentials.email), credentials.password)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Issue a new access and refresh pair from a valid refresh JWT."""
    tokens = await service.refresh(body.refresh_token)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
