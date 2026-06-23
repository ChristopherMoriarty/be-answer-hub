import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class NodeDetailResponse(BaseModel):
    """Full node payload including markdown content."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    content_md: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class NodeTreeItem(BaseModel):
    """Node metadata for sidebar tree rendering."""

    id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    sort_order: int
    has_content: bool
    children: Annotated[list["NodeTreeItem"], Field(default_factory=list)]


class NodeTreeResponse(BaseModel):
    """Nested tree of all nodes without markdown content."""

    items: list[NodeTreeItem]


NodeTreeItem.model_rebuild()
