class ServiceError(Exception):
    """Base class for service-layer errors mapped to HTTP responses."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundServiceError(ServiceError):
    """Resource was not found."""

    status_code = 404


class ConflictServiceError(ServiceError):
    """Request conflicts with current resource state."""

    status_code = 409
