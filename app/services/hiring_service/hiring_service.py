import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hiring import HiringBoard, HiringProcess, HiringStepValue
from app.repositories.hiring_repository import HiringRepository

from .helpers import (
    UNSET,
    apply_process_updates,
    apply_rejected_on_failed_step,
    create_default_columns,
    ensure_missing_default_columns,
    ensure_step_belongs_to_process,
    get_board_or_raise,
    get_column_for_board,
    get_process_or_raise,
    normalize_custom_title,
    resolve_offer_details,
    validate_column_reorder,
    validate_step_status,
)


class HiringService:
    """Business logic for hiring boards."""

    def __init__(self, session: AsyncSession, repository: HiringRepository) -> None:
        self._session = session
        self._repository = repository

    async def list_boards(self) -> list[HiringBoard]:
        return await self._repository.list_boards()

    async def get_board(self, board_id: uuid.UUID) -> HiringBoard:
        board = await get_board_or_raise(self._repository, board_id)
        if await ensure_missing_default_columns(self._repository, board):
            await self._session.commit()
            board = await get_board_or_raise(self._repository, board_id)
        return board

    async def create_board(self, *, title: str) -> HiringBoard:
        sort_order = await self._repository.get_next_board_sort_order()
        board = await self._repository.create_board(title=title, sort_order=sort_order)
        await create_default_columns(self._repository, board.id)
        await self._session.commit()
        return await self.get_board(board.id)

    async def update_board(self, board_id: uuid.UUID, *, title: str) -> HiringBoard:
        board = await self.get_board(board_id)
        board.title = title
        await self._repository.save_board(board)
        await self._session.commit()
        return await self.get_board(board_id)

    async def delete_board(self, board_id: uuid.UUID) -> None:
        board = await self.get_board(board_id)
        await self._repository.delete_board(board)
        await self._session.commit()

    async def add_column(
        self,
        board_id: uuid.UUID,
        *,
        step_kind: str,
        custom_title: str | None = None,
    ) -> HiringBoard:
        normalized_title = normalize_custom_title(step_kind, custom_title)
        await self.get_board(board_id)
        sort_order = await self._repository.get_next_column_sort_order(board_id)
        await self._repository.create_column(
            board_id=board_id,
            step_kind=step_kind,
            custom_title=normalized_title,
            sort_order=sort_order,
        )
        await self._session.commit()
        return await self.get_board(board_id)

    async def delete_column(
        self, board_id: uuid.UUID, column_id: uuid.UUID
    ) -> HiringBoard:
        board = await self.get_board(board_id)
        column = await get_column_for_board(self._repository, board, column_id)
        await self._repository.delete_column(column)
        await self._session.commit()
        return await self.get_board(board_id)

    async def reorder_columns(
        self,
        board_id: uuid.UUID,
        ordered_ids: list[uuid.UUID],
    ) -> HiringBoard:
        board = await self.get_board(board_id)
        validate_column_reorder(board, ordered_ids)
        await self._repository.reorder_columns(board_id, ordered_ids)
        await self._session.commit()
        return await self.get_board(board_id)

    async def create_process(
        self,
        board_id: uuid.UUID,
        *,
        company: str,
        source: str = "",
        result: str = "in_progress",
        offer_details: str | None = None,
        notes: str | None = None,
    ) -> HiringBoard:
        await self.get_board(board_id)
        sort_order = await self._repository.get_next_process_sort_order(board_id)
        await self._repository.create_process(
            board_id=board_id,
            company=company,
            source=source,
            result=result,
            offer_details=resolve_offer_details(result, offer_details),
            notes=notes,
            sort_order=sort_order,
        )
        await self._session.commit()
        return await self.get_board(board_id)

    async def update_process(
        self,
        process_id: uuid.UUID,
        *,
        company: str | Any = UNSET,
        source: str | Any = UNSET,
        result: str | Any = UNSET,
        offer_details: str | None | Any = UNSET,
        notes: str | None | Any = UNSET,
    ) -> HiringProcess:
        process = await get_process_or_raise(self._repository, process_id)
        apply_process_updates(
            process,
            company=company,
            source=source,
            result=result,
            offer_details=offer_details,
            notes=notes,
        )
        process = await self._repository.save_process(process)
        await self._session.commit()
        return process

    async def delete_process(self, process_id: uuid.UUID) -> None:
        process = await get_process_or_raise(self._repository, process_id)
        await self._repository.delete_process(process)
        await self._session.commit()

    async def upsert_step_value(
        self,
        process_id: uuid.UUID,
        column_id: uuid.UUID,
        *,
        status: str,
        event_date: date | None = None,
    ) -> HiringStepValue:
        validate_step_status(status)
        process = await get_process_or_raise(self._repository, process_id)
        column = await ensure_step_belongs_to_process(
            self._repository, process, column_id
        )

        value = await self._repository.upsert_step_value(
            process_id=process_id,
            column_id=column_id,
            status=status,
            event_date=event_date,
        )
        apply_rejected_on_failed_step(process, column, status)
        await self._repository.save_process(process)
        await self._session.commit()
        return value
