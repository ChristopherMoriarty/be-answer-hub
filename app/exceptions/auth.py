from app.exceptions.base import ServiceError


class UnauthorizedServiceError(ServiceError):
    """Credentials or a token were rejected."""

    status_code = 401
