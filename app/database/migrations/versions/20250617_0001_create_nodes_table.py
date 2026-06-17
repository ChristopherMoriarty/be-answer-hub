"""create nodes table

Revision ID: 20250617_0001
Revises:
Create Date: 2025-06-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250617_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["parent_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_id", "title", name="uq_nodes_parent_title"),
    )
    op.create_index("ix_nodes_parent_id", "nodes", ["parent_id"], unique=False)
    op.create_index("ix_nodes_parent_sort_order", "nodes", ["parent_id", "sort_order"], unique=False)
    op.create_index(
        "uq_nodes_root_title",
        "nodes",
        ["title"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_nodes_root_title", table_name="nodes", postgresql_where=sa.text("parent_id IS NULL"))
    op.drop_index("ix_nodes_parent_sort_order", table_name="nodes")
    op.drop_index("ix_nodes_parent_id", table_name="nodes")
    op.drop_table("nodes")
