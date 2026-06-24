import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HiringBoard(Base):
    """A role-specific hiring tracker table, e.g. Python applications."""

    __tablename__ = "hiring_board"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    columns: Mapped[list["HiringBoardColumn"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="HiringBoardColumn.sort_order",
    )
    processes: Mapped[list["HiringProcess"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="HiringProcess.sort_order",
    )


class HiringBoardColumn(Base):
    """A step column in a hiring board."""

    __tablename__ = "hiring_board_column"

    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hiring_board.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_kind: Mapped[str] = mapped_column(Text, nullable=False)
    custom_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    board: Mapped[HiringBoard] = relationship(back_populates="columns")
    step_values: Mapped[list["HiringStepValue"]] = relationship(
        back_populates="column",
        cascade="all, delete-orphan",
    )


class HiringProcess(Base):
    """One hiring process (table row) at a company."""

    __tablename__ = "hiring_process"

    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hiring_board.id", ondelete="CASCADE"),
        nullable=False,
    )
    company: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    result: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="in_progress",
        server_default="in_progress",
    )
    offer_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    board: Mapped[HiringBoard] = relationship(back_populates="processes")
    step_values: Mapped[list["HiringStepValue"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
    )


class HiringStepValue(Base):
    """Cell value for a process step column."""

    __tablename__ = "hiring_step_value"
    __table_args__ = (
        UniqueConstraint(
            "process_id", "column_id", name="uq_hiring_step_value_process_column"
        ),
    )

    process_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hiring_process.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hiring_board_column.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="empty", server_default="empty"
    )
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    process: Mapped[HiringProcess] = relationship(back_populates="step_values")
    column: Mapped[HiringBoardColumn] = relationship(back_populates="step_values")
