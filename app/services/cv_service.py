import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.minio import MinioClient
from app.exceptions.cv import CvNotFoundError, InvalidCvFileError
from app.models.cv import Cv
from app.repositories.cv_repository import CvRepository

PDF_CONTENT_TYPE = "application/pdf"
MAX_CV_FILE_SIZE = 10 * 1024 * 1024

UNSET: Any = object()


def build_storage_key(cv_id: uuid.UUID) -> str:
    return f"cv/{cv_id}.pdf"


def validate_pdf_file(*, content_type: str | None, file_size: int) -> None:
    if content_type != PDF_CONTENT_TYPE:
        raise InvalidCvFileError("Only PDF files are allowed")

    if file_size <= 0:
        raise InvalidCvFileError("Uploaded file is empty")

    if file_size > MAX_CV_FILE_SIZE:
        raise InvalidCvFileError("PDF file exceeds 10 MB limit")


class CvService:
    """Business logic for CV PDF storage."""

    def __init__(
        self,
        session: AsyncSession,
        repository: CvRepository,
        minio: MinioClient,
    ) -> None:
        self._session = session
        self._repository = repository
        self._minio = minio

    async def list_cv(self) -> list[Cv]:
        """Return all stored CV versions."""
        return await self._repository.list_all()

    async def get_cv(self, cv_id: uuid.UUID) -> Cv:
        """Return a CV record or raise if it does not exist."""
        cv = await self._repository.get_by_id(cv_id)
        if cv is None:
            raise CvNotFoundError(f"CV {cv_id} not found")
        return cv

    async def upload_cv(
        self,
        *,
        title: str,
        original_filename: str,
        content_type: str | None,
        body: bytes,
        notes: str | None = None,
        is_current: bool = False,
    ) -> Cv:
        """Upload a PDF to object storage and persist metadata."""
        validate_pdf_file(content_type=content_type, file_size=len(body))

        cv_id = uuid.uuid4()
        storage_key = build_storage_key(cv_id)

        if is_current:
            await self._repository.unset_all_current()

        await self._minio.put_object(
            storage_key,
            body,
            content_type=PDF_CONTENT_TYPE,
        )

        try:
            cv = await self._repository.create(
                cv_id=cv_id,
                title=title,
                original_filename=original_filename,
                storage_key=storage_key,
                file_size=len(body),
                mime_type=PDF_CONTENT_TYPE,
                is_current=is_current,
                notes=notes,
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            await self._minio.delete_object(storage_key)
            raise

        return cv

    async def update_cv(
        self,
        cv_id: uuid.UUID,
        *,
        title: str | Any = UNSET,
        notes: str | None | Any = UNSET,
        is_current: bool | Any = UNSET,
    ) -> Cv:
        """Update CV metadata."""
        cv = await self.get_cv(cv_id)

        if title is not UNSET:
            cv.title = title

        if notes is not UNSET:
            cv.notes = notes

        if is_current is not UNSET:
            if is_current and not cv.is_current:
                await self._repository.unset_all_current()
            cv.is_current = is_current

        cv = await self._repository.save(cv)
        await self._session.commit()
        return cv

    async def delete_cv(self, cv_id: uuid.UUID) -> None:
        """Delete a CV record and its object from storage."""
        cv = await self.get_cv(cv_id)
        storage_key = cv.storage_key

        await self._minio.delete_object(storage_key)
        await self._repository.delete(cv)
        await self._session.commit()

    async def get_download_url(self, cv_id: uuid.UUID) -> str:
        """Return a presigned download URL for a CV PDF."""
        cv = await self.get_cv(cv_id)
        return await self._minio.presigned_get_url(cv.storage_key)

    async def get_cv_file(self, cv_id: uuid.UUID) -> tuple[Cv, bytes]:
        """Return CV metadata and PDF bytes for inline preview."""
        cv = await self.get_cv(cv_id)
        body = await self._minio.get_object(cv.storage_key)
        return cv, body
