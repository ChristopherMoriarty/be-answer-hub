import uuid

from pydantic import BaseModel, Field


class CreateHiringBoardRequest(BaseModel):
    title: str = Field(min_length=1)


class UpdateHiringBoardRequest(BaseModel):
    title: str = Field(min_length=1)


class AddHiringColumnRequest(BaseModel):
    step_kind: str
    custom_title: str | None = None


class CreateHiringProcessRequest(BaseModel):
    company: str = Field(min_length=1)
    source: str = ""
    result: str = "in_progress"
    offer_details: str | None = None
    notes: str | None = None


class UpdateHiringProcessRequest(BaseModel):
    company: str | None = None
    source: str | None = None
    result: str | None = None
    offer_details: str | None = None
    notes: str | None = None


class UpsertHiringStepValueRequest(BaseModel):
    status: str
    event_date: str | None = None


class ReorderHiringColumnsRequest(BaseModel):
    ordered_ids: list[uuid.UUID] = Field(min_length=1)
