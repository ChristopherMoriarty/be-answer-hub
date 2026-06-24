import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.constants import STEP_KIND_LABELS


class HiringBoardSummaryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class HiringBoardListResponse(BaseModel):
    items: list[HiringBoardSummaryResponse] = Field(default_factory=list)


class HiringColumnResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    step_kind: str
    custom_title: str | None
    title: str
    sort_order: int


class HiringStepValueResponse(BaseModel):
    model_config = {"from_attributes": True}

    column_id: uuid.UUID
    status: str
    event_date: date | None


class HiringProcessResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company: str
    source: str
    result: str
    offer_details: str | None
    notes: str | None
    sort_order: int
    cells: list[HiringStepValueResponse] = Field(default_factory=list)


class HiringBoardDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    sort_order: int
    columns: list[HiringColumnResponse] = Field(default_factory=list)
    processes: list[HiringProcessResponse] = Field(default_factory=list)
    step_kinds: dict[str, str] = Field(default_factory=lambda: dict(STEP_KIND_LABELS))


class HiringProcessRowResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company: str
    source: str
    result: str
    offer_details: str | None
    notes: str | None
    sort_order: int
