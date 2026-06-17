import uuid
from typing import Annotated

from pydantic import BaseModel, Field


class CreateNodeRequest(BaseModel):
    """Payload for creating a section or leaf node."""

    title: Annotated[str, Field(min_length=1, max_length=500)]
    parent_id: Annotated[uuid.UUID | None, Field(default=None)] = None
    content_md: Annotated[str | None, Field(default=None)] = None
    sort_order: Annotated[int | None, Field(default=None, ge=0)] = None


class UpdateNodeRequest(BaseModel):
    """Partial update payload for an existing node."""

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=500)] = (
        None
    )
    content_md: Annotated[str | None, Field(default=None)] = None
    sort_order: Annotated[int | None, Field(default=None, ge=0)] = None


class MoveNodeRequest(BaseModel):
    """Payload for moving a node to another parent."""

    parent_id: uuid.UUID | None
    sort_order: Annotated[int | None, Field(default=None, ge=0)] = None
