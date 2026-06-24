import uuid

from fastapi import APIRouter, Depends, status

from app.core.constants import API_PREFIX
from app.dependencies.services import get_hiring_service
from app.schemas.requests.hiring import (
    AddHiringColumnRequest,
    CreateHiringBoardRequest,
    CreateHiringProcessRequest,
    ReorderHiringColumnsRequest,
    UpdateHiringBoardRequest,
    UpdateHiringProcessRequest,
    UpsertHiringStepValueRequest,
)
from app.schemas.responses.hiring import (
    HiringBoardDetailResponse,
    HiringBoardListResponse,
    HiringBoardSummaryResponse,
    HiringProcessRowResponse,
    HiringStepValueResponse,
)
from app.services.hiring_service import HiringService
from app.utils.hiring import build_board_detail, parse_event_date

router = APIRouter(prefix=f"{API_PREFIX}/hiring", tags=["hiring"])


@router.get("/boards", response_model=HiringBoardListResponse)
async def list_boards(
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardListResponse:
    boards = await service.list_boards()
    return HiringBoardListResponse(
        items=[HiringBoardSummaryResponse.model_validate(board) for board in boards]
    )


@router.post(
    "/boards",
    response_model=HiringBoardDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_board(
    body: CreateHiringBoardRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.create_board(title=body.title.strip())
    return build_board_detail(board)


@router.get("/boards/{board_id}", response_model=HiringBoardDetailResponse)
async def get_board(
    board_id: uuid.UUID,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.get_board(board_id)
    return build_board_detail(board)


@router.patch("/boards/{board_id}", response_model=HiringBoardDetailResponse)
async def update_board(
    board_id: uuid.UUID,
    body: UpdateHiringBoardRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.update_board(board_id, title=body.title.strip())
    return build_board_detail(board)


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: uuid.UUID,
    service: HiringService = Depends(get_hiring_service),
) -> None:
    await service.delete_board(board_id)


@router.post("/boards/{board_id}/columns", response_model=HiringBoardDetailResponse)
async def add_column(
    board_id: uuid.UUID,
    body: AddHiringColumnRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.add_column(
        board_id,
        step_kind=body.step_kind,
        custom_title=body.custom_title,
    )
    return build_board_detail(board)


@router.put(
    "/boards/{board_id}/columns/reorder", response_model=HiringBoardDetailResponse
)
async def reorder_columns(
    board_id: uuid.UUID,
    body: ReorderHiringColumnsRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.reorder_columns(board_id, body.ordered_ids)
    return build_board_detail(board)


@router.delete(
    "/boards/{board_id}/columns/{column_id}", response_model=HiringBoardDetailResponse
)
async def delete_column(
    board_id: uuid.UUID,
    column_id: uuid.UUID,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.delete_column(board_id, column_id)
    return build_board_detail(board)


@router.post("/boards/{board_id}/processes", response_model=HiringBoardDetailResponse)
async def create_process(
    board_id: uuid.UUID,
    body: CreateHiringProcessRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringBoardDetailResponse:
    board = await service.create_process(
        board_id,
        company=body.company.strip(),
        source=body.source.strip(),
        result=body.result,
        offer_details=body.offer_details,
        notes=body.notes,
    )
    return build_board_detail(board)


@router.patch("/processes/{process_id}", response_model=HiringProcessRowResponse)
async def update_process(
    process_id: uuid.UUID,
    body: UpdateHiringProcessRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringProcessRowResponse:
    process = await service.update_process(
        process_id,
        **body.model_dump(exclude_unset=True),
    )
    return HiringProcessRowResponse.model_validate(process)


@router.delete("/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process(
    process_id: uuid.UUID,
    service: HiringService = Depends(get_hiring_service),
) -> None:
    await service.delete_process(process_id)


@router.put(
    "/processes/{process_id}/cells/{column_id}", response_model=HiringStepValueResponse
)
async def upsert_step_value(
    process_id: uuid.UUID,
    column_id: uuid.UUID,
    body: UpsertHiringStepValueRequest,
    service: HiringService = Depends(get_hiring_service),
) -> HiringStepValueResponse:
    value = await service.upsert_step_value(
        process_id,
        column_id,
        status=body.status,
        event_date=parse_event_date(body.event_date),
    )
    return HiringStepValueResponse(
        column_id=value.column_id,
        status=value.status,
        event_date=value.event_date,
    )
