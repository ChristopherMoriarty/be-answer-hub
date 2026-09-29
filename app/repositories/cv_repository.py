import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cv import Cv


class CvRepository:
    """Data access layer for stored CV PDFs."""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self._session = session
        self._user_id = user_id

    async def get_by_id(self, cv_id: uuid.UUID) -> Cv | None:
        """Return a CV record by primary key."""
        stmt = select(Cv).where(Cv.id == cv_id, Cv.user_id == self._user_id)
        return await self._session.scalar(stmt)

    async def list_all(self) -> list[Cv]:
        """Return all CV records, newest first."""
        stmt = (
            select(Cv).where(Cv.user_id == self._user_id).order_by(Cv.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def unset_all_current(self) -> None:
        """Clear the current flag from this user's CV records."""
        stmt = (
            update(Cv)
            .where(Cv.user_id == self._user_id, Cv.is_current.is_(True))
            .values(is_current=False)
        )
        await self._session.execute(stmt)

    async def create(
        self,
        *,
        cv_id: uuid.UUID,
        title: str,
        original_filename: str,
        storage_key: str,
        file_size: int,
        mime_type: str,
        is_current: bool = False,
        notes: str | None = None,
    ) -> Cv:
        """Persist a new CV record."""
        cv = Cv(
            id=cv_id,
            user_id=self._user_id,
            title=title,
            original_filename=original_filename,
            storage_key=storage_key,
            file_size=file_size,
            mime_type=mime_type,
            is_current=is_current,
            notes=notes,
        )
        self._session.add(cv)
        await self._session.flush()
        await self._session.refresh(cv)
        return cv

    async def save(self, cv: Cv) -> Cv:
        """Flush pending changes for an existing CV record."""
        self._session.add(cv)
        await self._session.flush()
        await self._session.refresh(cv)
        return cv

    async def delete(self, cv: Cv) -> None:
        """Delete a CV record."""
        await self._session.delete(cv)
        await self._session.flush()
