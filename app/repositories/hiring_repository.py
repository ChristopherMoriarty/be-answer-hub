import uuid
from datetime import date

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hiring import (
    HiringBoard,
    HiringBoardColumn,
    HiringProcess,
    HiringStepValue,
)


class HiringRepository:
    """Data access for hiring boards and processes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_boards(self) -> list[HiringBoard]:
        stmt = select(HiringBoard).order_by(
            HiringBoard.sort_order, HiringBoard.created_at
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_board_by_id(self, board_id: uuid.UUID) -> HiringBoard | None:
        stmt = (
            select(HiringBoard)
            .where(HiringBoard.id == board_id)
            .options(
                selectinload(HiringBoard.columns),
                selectinload(HiringBoard.processes).selectinload(
                    HiringProcess.step_values
                ),
            )
            .execution_options(populate_existing=True)
        )
        return await self._session.scalar(stmt)

    async def get_next_board_sort_order(self) -> int:
        stmt = select(func.coalesce(func.max(HiringBoard.sort_order), -1))
        max_order = await self._session.scalar(stmt)
        return (-1 if max_order is None else int(max_order)) + 1

    async def create_board(self, *, title: str, sort_order: int) -> HiringBoard:
        board = HiringBoard(title=title, sort_order=sort_order)
        self._session.add(board)
        await self._session.flush()
        await self._session.refresh(board)
        return board

    async def save_board(self, board: HiringBoard) -> HiringBoard:
        self._session.add(board)
        await self._session.flush()
        await self._session.refresh(board)
        return board

    async def delete_board(self, board: HiringBoard) -> None:
        await self._session.delete(board)
        await self._session.flush()

    async def get_column_by_id(self, column_id: uuid.UUID) -> HiringBoardColumn | None:
        return await self._session.get(HiringBoardColumn, column_id)

    async def get_next_column_sort_order(self, board_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.max(HiringBoardColumn.sort_order), -1)).where(
            HiringBoardColumn.board_id == board_id
        )
        max_order = await self._session.scalar(stmt)
        return (-1 if max_order is None else int(max_order)) + 1

    async def create_column(
        self,
        *,
        board_id: uuid.UUID,
        step_kind: str,
        custom_title: str | None,
        sort_order: int,
    ) -> HiringBoardColumn:
        column = HiringBoardColumn(
            board_id=board_id,
            step_kind=step_kind,
            custom_title=custom_title,
            sort_order=sort_order,
        )
        self._session.add(column)
        await self._session.flush()
        await self._session.refresh(column)
        return column

    async def delete_column(self, column: HiringBoardColumn) -> None:
        await self._session.delete(column)
        await self._session.flush()

    async def reorder_columns(
        self, board_id: uuid.UUID, ordered_ids: list[uuid.UUID]
    ) -> None:
        for index, column_id in enumerate(ordered_ids):
            stmt = (
                update(HiringBoardColumn)
                .where(
                    HiringBoardColumn.id == column_id,
                    HiringBoardColumn.board_id == board_id,
                )
                .values(sort_order=index)
            )
            await self._session.execute(stmt)

    async def get_process_by_id(self, process_id: uuid.UUID) -> HiringProcess | None:
        stmt = (
            select(HiringProcess)
            .where(HiringProcess.id == process_id)
            .options(selectinload(HiringProcess.step_values))
        )
        return await self._session.scalar(stmt)

    async def get_next_process_sort_order(self, board_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.max(HiringProcess.sort_order), -1)).where(
            HiringProcess.board_id == board_id
        )
        max_order = await self._session.scalar(stmt)
        return (-1 if max_order is None else int(max_order)) + 1

    async def create_process(
        self,
        *,
        board_id: uuid.UUID,
        company: str,
        source: str,
        result: str,
        offer_details: str | None,
        notes: str | None,
        sort_order: int,
    ) -> HiringProcess:
        process = HiringProcess(
            board_id=board_id,
            company=company,
            source=source,
            result=result,
            offer_details=offer_details,
            notes=notes,
            sort_order=sort_order,
        )
        self._session.add(process)
        await self._session.flush()
        await self._session.refresh(process)
        return process

    async def save_process(self, process: HiringProcess) -> HiringProcess:
        self._session.add(process)
        await self._session.flush()
        await self._session.refresh(process)
        return process

    async def delete_process(self, process: HiringProcess) -> None:
        await self._session.delete(process)
        await self._session.flush()

    async def get_step_value(
        self,
        *,
        process_id: uuid.UUID,
        column_id: uuid.UUID,
    ) -> HiringStepValue | None:
        stmt = select(HiringStepValue).where(
            HiringStepValue.process_id == process_id,
            HiringStepValue.column_id == column_id,
        )
        return await self._session.scalar(stmt)

    async def upsert_step_value(
        self,
        *,
        process_id: uuid.UUID,
        column_id: uuid.UUID,
        status: str,
        event_date: date | None,
    ) -> HiringStepValue:
        existing = await self.get_step_value(process_id=process_id, column_id=column_id)
        if existing is None:
            value = HiringStepValue(
                process_id=process_id,
                column_id=column_id,
                status=status,
                event_date=event_date,
            )
            self._session.add(value)
        else:
            existing.status = status
            existing.event_date = event_date
            value = existing
        await self._session.flush()
        await self._session.refresh(value)
        return value

    async def clear_step_values_for_column(self, column_id: uuid.UUID) -> None:
        stmt = delete(HiringStepValue).where(HiringStepValue.column_id == column_id)
        await self._session.execute(stmt)
