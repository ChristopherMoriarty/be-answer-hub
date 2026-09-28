import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    """Account stored in the database. There is no registration route."""

    __tablename__ = "users"

    if TYPE_CHECKING:
        id: uuid.UUID
        email: str
        hashed_password: str
        is_active: bool
        is_superuser: bool
        is_verified: bool
    else:
        email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
        hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
        is_active: Mapped[bool] = mapped_column(
            Boolean, nullable=False, default=True, server_default="true"
        )
        is_superuser: Mapped[bool] = mapped_column(
            Boolean, nullable=False, default=False, server_default="false"
        )
        is_verified: Mapped[bool] = mapped_column(
            Boolean, nullable=False, default=False, server_default="false"
        )
