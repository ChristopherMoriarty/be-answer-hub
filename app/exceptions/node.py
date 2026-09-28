from app.exceptions.base import ConflictServiceError, NotFoundServiceError, ServiceError


class NodeNotFoundError(NotFoundServiceError):
    """Node does not exist."""


class DuplicateNodeTitleError(ConflictServiceError):
    """Another sibling already uses this title."""


class NodeHasContentError(ConflictServiceError):
    """Node already stores an answer and cannot have children."""


class InvalidNodeMoveError(ConflictServiceError):
    """Node cannot be moved to the requested parent."""


class InvalidReorderError(ConflictServiceError):
    """Reorder payload is invalid."""


class InvalidNodeValueError(ServiceError):
    """Node payload values are invalid."""

    status_code = 422


class InvalidContentLanguageError(InvalidNodeValueError):
    """Requested content language is not supported."""


class NodeTranslationNotFoundError(NotFoundServiceError):
    """Translation for the requested language does not exist."""


class LastTranslationError(ConflictServiceError):
    """Cannot remove the last translation from a leaf node."""
