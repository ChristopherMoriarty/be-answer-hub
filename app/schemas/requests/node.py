import uuid
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class CreateNodeRequest(BaseModel):
    """Payload for creating a section or leaf node."""

    title: Annotated[str, Field(min_length=1, max_length=500)]
    parent_id: Annotated[uuid.UUID | None, Field(default=None)] = None
    content_md: Annotated[str | None, Field(default=None)] = None
    language: Annotated[
        str | None, Field(default=None, min_length=2, max_length=16)
    ] = None
    sort_order: Annotated[int | None, Field(default=None, ge=0)] = None

    @model_validator(mode="after")
    def validate_content_and_language(self) -> "CreateNodeRequest":
        has_content = self.content_md is not None and bool(self.content_md.strip())
        has_language = self.language is not None
        if has_content and not has_language:
            raise ValueError("language is required when content_md is provided")
        if has_language and not has_content:
            raise ValueError("content_md is required when language is provided")
        return self


class UpdateNodeRequest(BaseModel):
    """Partial update payload for an existing node."""

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=500)] = (
        None
    )
    sort_order: Annotated[int | None, Field(default=None, ge=0)] = None


class UpsertNodeTranslationRequest(BaseModel):
    """Payload for creating or updating a language version of a node answer."""

    content_md: Annotated[str, Field(min_length=1)]


class MoveNodeRequest(BaseModel):
    """Payload for moving a node to another parent."""

    parent_id: uuid.UUID | None
    sort_order: Annotated[int | None, Field(default=None, ge=0)] = None


class ReorderNodesRequest(BaseModel):
    """Payload for reordering siblings and optionally moving nodes into a parent."""

    parent_id: uuid.UUID | None
    ordered_ids: Annotated[list[uuid.UUID], Field(min_length=1)]
