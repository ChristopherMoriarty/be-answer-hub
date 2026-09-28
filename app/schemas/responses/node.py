import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.core.constants import CONTENT_LANGUAGE_LABELS
from app.models.node import Node


class NodeTranslationResponse(BaseModel):
    """One language version of a node answer."""

    model_config = {"from_attributes": True}

    language: str
    content_md: str
    created_at: datetime
    updated_at: datetime


class NodeDetailResponse(BaseModel):
    """Full node payload including translations."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    sort_order: int
    translations: list[NodeTranslationResponse]
    languages: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_node(cls, node: Node) -> "NodeDetailResponse":
        translations = [
            NodeTranslationResponse.model_validate(item) for item in node.translations
        ]
        return cls(
            id=node.id,
            parent_id=node.parent_id,
            title=node.title,
            sort_order=node.sort_order,
            translations=translations,
            languages=[item.language for item in translations],
            created_at=node.created_at,
            updated_at=node.updated_at,
        )


class NodeTreeItem(BaseModel):
    """Node metadata for sidebar tree rendering."""

    id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    sort_order: int
    has_content: bool
    languages: list[str]
    children: Annotated[list["NodeTreeItem"], Field(default_factory=list)]


class NodeTreeResponse(BaseModel):
    """Nested tree of all nodes without markdown content."""

    items: list[NodeTreeItem]
    content_languages: dict[str, str] = CONTENT_LANGUAGE_LABELS


NodeTreeItem.model_rebuild()
