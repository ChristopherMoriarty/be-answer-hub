from pydantic import BaseModel


class UpdateCvRequest(BaseModel):
    """Partial update payload for CV metadata."""

    title: str | None = None
    notes: str | None = None
    is_current: bool | None = None
