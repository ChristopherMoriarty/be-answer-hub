import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.models.node_translation import NodeTranslation


class Node(Base):
    """Hierarchical topic node. Leaf nodes store markdown answers per language."""

    __tablename__ = "nodes"
    __table_args__ = (
        UniqueConstraint("parent_id", "title", name="uq_nodes_parent_title"),
        Index("ix_nodes_parent_sort_order", "parent_id", "sort_order"),
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    parent: Mapped["Node | None"] = relationship(
        "Node",
        remote_side="Node.id",
        back_populates="children",
    )
    children: Mapped["Sequence[Node]"] = relationship(
        "Node",
        back_populates="parent",
        order_by="Node.sort_order",
        passive_deletes=True,
    )
    translations: Mapped[list["NodeTranslation"]] = relationship(
        "NodeTranslation",
        back_populates="node",
        cascade="all, delete-orphan",
        order_by="NodeTranslation.created_at",
        passive_deletes=True,
    )

    @property
    def has_content(self) -> bool:
        return bool(self.translations)

    def translation_for(self, language: str) -> "NodeTranslation | None":
        for translation in self.translations:
            if translation.language == language:
                return translation
        return None
