from app.exceptions.base import ConflictServiceError, NotFoundServiceError


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
