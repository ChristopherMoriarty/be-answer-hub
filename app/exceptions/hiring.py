from app.exceptions.base import NotFoundServiceError, ServiceError


class HiringBoardNotFoundError(NotFoundServiceError):
    """Hiring board does not exist."""


class HiringColumnNotFoundError(NotFoundServiceError):
    """Hiring board column does not exist."""


class HiringProcessNotFoundError(NotFoundServiceError):
    """Hiring process does not exist."""


class InvalidHiringValueError(ServiceError):
    """Invalid hiring field value."""

    status_code = 422
