import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.node import Node


class NodeTranslation(Base):
    """Markdown answer content for a node in a specific language."""

    __tablename__ = "node_translations"
    __table_args__ = (
        UniqueConstraint(
            "node_id",
            "language",
            name="uq_node_translations_node_language",
        ),
    )

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(Text, nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)

    node: Mapped["Node"] = relationship("Node", back_populates="translations")
