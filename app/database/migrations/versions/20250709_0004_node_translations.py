"""add node translations

Revision ID: 20250709_0004
Revises: 20250624_0003
Create Date: 2025-07-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250709_0004"
down_revision: Union[str, None] = "20250624_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "node_id",
            "language",
            name="uq_node_translations_node_language",
        ),
    )
    op.create_index(
        "ix_node_translations_node_id",
        "node_translations",
        ["node_id"],
        unique=False,
    )
    op.drop_column("nodes", "content_md")


def downgrade() -> None:
    op.add_column("nodes", sa.Column("content_md", sa.Text(), nullable=True))
    op.drop_index("ix_node_translations_node_id", table_name="node_translations")
    op.drop_table("node_translations")
