from app.exceptions.base import NotFoundServiceError, ServiceError


class CvNotFoundError(NotFoundServiceError):
    """CV does not exist."""


class InvalidCvFileError(ServiceError):
    """Uploaded file is not a valid CV PDF."""

    status_code = 422
