import uuid
from typing import Any

from app.core.constants import (
    ALLOWED_RESULTS,
    ALLOWED_STEP_KINDS,
    ALLOWED_STEP_STATUSES,
    DEFAULT_BOARD_COLUMN_KINDS,
)
from app.exceptions.hiring import (
    HiringBoardNotFoundError,
    HiringColumnNotFoundError,
    HiringProcessNotFoundError,
    InvalidHiringValueError,
)
from app.models.hiring import HiringBoard, HiringBoardColumn, HiringProcess
from app.repositories.hiring_repository import HiringRepository

UNSET: Any = object()


def validate_step_kind(step_kind: str) -> None:
    if step_kind not in ALLOWED_STEP_KINDS:
        raise InvalidHiringValueError(f"Unknown step kind: {step_kind}")


def validate_result(result: str) -> None:
    if result not in ALLOWED_RESULTS:
        raise InvalidHiringValueError(f"Unknown result: {result}")


def validate_step_status(status: str) -> None:
    if status not in ALLOWED_STEP_STATUSES:
        raise InvalidHiringValueError(f"Unknown step status: {status}")


def normalize_custom_title(step_kind: str, custom_title: str | None) -> str | None:
    validate_step_kind(step_kind)
    if step_kind == "custom" and not (custom_title and custom_title.strip()):
        raise InvalidHiringValueError("Custom step requires a title")
    return custom_title.strip() if custom_title else None


def resolve_offer_details(result: str, offer_details: str | None) -> str | None:
    validate_result(result)
    if result != "offer":
        return None
    return offer_details


async def get_board_or_raise(
    repository: HiringRepository,
    board_id: uuid.UUID,
) -> HiringBoard:
    board = await repository.get_board_by_id(board_id)
    if board is None:
        raise HiringBoardNotFoundError(f"Hiring board {board_id} not found")
    return board


async def get_process_or_raise(
    repository: HiringRepository,
    process_id: uuid.UUID,
) -> HiringProcess:
    process = await repository.get_process_by_id(process_id)
    if process is None:
        raise HiringProcessNotFoundError(f"Process {process_id} not found")
    return process


async def get_column_for_board(
    repository: HiringRepository,
    board: HiringBoard,
    column_id: uuid.UUID,
) -> HiringBoardColumn:
    column = await repository.get_column_by_id(column_id)
    if column is None or column.board_id != board.id:
        raise HiringColumnNotFoundError(f"Column {column_id} not found")
    return column


def apply_process_updates(
    process: HiringProcess,
    *,
    company: str | Any = UNSET,
    source: str | Any = UNSET,
    result: str | Any = UNSET,
    offer_details: str | None | Any = UNSET,
    notes: str | None | Any = UNSET,
) -> None:
    if company is not UNSET:
        process.company = company
    if source is not UNSET:
        process.source = source
    if result is not UNSET:
        validate_result(result)
        process.result = result
    if offer_details is not UNSET:
        process.offer_details = offer_details
    if notes is not UNSET:
        process.notes = notes

    if process.result != "offer":
        process.offer_details = None


def ensure_unique_reorder_ids(ordered_ids: list[uuid.UUID]) -> None:
    if len(ordered_ids) != len(set(ordered_ids)):
        raise InvalidHiringValueError("Reorder payload contains duplicate column ids")


def validate_column_reorder(board: HiringBoard, ordered_ids: list[uuid.UUID]) -> None:
    ensure_unique_reorder_ids(ordered_ids)
    board_column_ids = {column.id for column in board.columns}
    if set(ordered_ids) != board_column_ids:
        raise InvalidHiringValueError(
            "Reorder payload must include all board columns exactly once"
        )


async def create_default_columns(
    repository: HiringRepository,
    board_id: uuid.UUID,
) -> None:
    for index, step_kind in enumerate(DEFAULT_BOARD_COLUMN_KINDS):
        await repository.create_column(
            board_id=board_id,
            step_kind=step_kind,
            custom_title=None,
            sort_order=index,
        )


async def ensure_missing_default_columns(
    repository: HiringRepository,
    board: HiringBoard,
) -> bool:
    """Add default step columns to boards created before defaults existed."""
    existing_kinds = {column.step_kind for column in board.columns}
    missing = [
        kind for kind in DEFAULT_BOARD_COLUMN_KINDS if kind not in existing_kinds
    ]
    if not missing:
        return False

    sort_order = await repository.get_next_column_sort_order(board.id)
    for offset, step_kind in enumerate(missing):
        await repository.create_column(
            board_id=board.id,
            step_kind=step_kind,
            custom_title=None,
            sort_order=sort_order + offset,
        )
    return True


async def ensure_step_belongs_to_process(
    repository: HiringRepository,
    process: HiringProcess,
    column_id: uuid.UUID,
) -> HiringBoardColumn:
    column = await repository.get_column_by_id(column_id)
    if column is None or column.board_id != process.board_id:
        raise HiringColumnNotFoundError(f"Column {column_id} not found")
    return column


def apply_rejected_on_failed_step(
    process: HiringProcess,
    column: HiringBoardColumn,
    status: str,
) -> None:
    if status != "failed" or column.step_kind == "applied":
        return
    process.result = "rejected"
    process.offer_details = None
