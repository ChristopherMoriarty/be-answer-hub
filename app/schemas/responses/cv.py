import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CvResponse(BaseModel):
    """CV metadata returned by the API."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    original_filename: str
    file_size: int
    mime_type: str
    is_current: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CvListResponse(BaseModel):
    """List of stored CV versions."""

    items: list[CvResponse] = Field(default_factory=list)
