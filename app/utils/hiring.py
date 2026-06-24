from datetime import date

from app.core.constants import STEP_KIND_LABELS
from app.models.hiring import HiringBoard, HiringBoardColumn
from app.schemas.responses.hiring import (
    HiringBoardDetailResponse,
    HiringColumnResponse,
    HiringProcessResponse,
    HiringStepValueResponse,
)


def column_title(column: HiringBoardColumn) -> str:
    if column.step_kind == "custom":
        return column.custom_title or "Custom"
    return STEP_KIND_LABELS.get(column.step_kind, column.step_kind)


def parse_event_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def build_board_detail(board: HiringBoard) -> HiringBoardDetailResponse:
    """Map a hiring board ORM graph to the API table response."""
    columns = sorted(board.columns, key=lambda item: item.sort_order)
    processes = sorted(board.processes, key=lambda item: item.sort_order)

    return HiringBoardDetailResponse(
        id=board.id,
        title=board.title,
        sort_order=board.sort_order,
        columns=[
            HiringColumnResponse(
                id=column.id,
                step_kind=column.step_kind,
                custom_title=column.custom_title,
                title=column_title(column),
                sort_order=column.sort_order,
            )
            for column in columns
        ],
        processes=[
            HiringProcessResponse(
                id=process.id,
                company=process.company,
                source=process.source,
                result=process.result,
                offer_details=process.offer_details,
                notes=process.notes,
                sort_order=process.sort_order,
                cells=[
                    HiringStepValueResponse(
                        column_id=cell.column_id,
                        status=cell.status,
                        event_date=cell.event_date,
                    )
                    for cell in process.step_values
                ],
            )
            for process in processes
        ],
    )
