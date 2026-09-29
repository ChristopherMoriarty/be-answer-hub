"""relate nodes, cv, and hiring boards to a user

Revision ID: 20250929_0006
Revises: 20250928_0005
Create Date: 2026-09-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250929_0006"
down_revision: Union[str, None] = "20250928_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("nodes", "cv", "hiring_board")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        )
        op.create_foreign_key(
            f"fk_{table}_user_id_users",
            table,
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])

    op.drop_index("uq_cv_single_current", table_name="cv")
    op.create_index(
        "uq_cv_single_current_per_user",
        "cv",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_cv_single_current_per_user", table_name="cv")
    op.create_index(
        "uq_cv_single_current",
        "cv",
        ["is_current"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )
    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_constraint(f"fk_{table}_user_id_users", table, type_="foreignkey")
        op.drop_column(table, "user_id")
