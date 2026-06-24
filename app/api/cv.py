import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response

from app.core.constants import API_PREFIX
from app.dependencies.services import get_cv_service
from app.schemas.requests.cv import UpdateCvRequest
from app.schemas.responses.cv import CvListResponse, CvResponse
from app.services.cv_service import CvService
from app.utils.content_disposition import (
    build_attachment_content_disposition,
    build_inline_content_disposition,
)

router = APIRouter(prefix=f"{API_PREFIX}/cv", tags=["cv"])


@router.get("", response_model=CvListResponse)
async def list_cv(service: CvService = Depends(get_cv_service)) -> CvListResponse:
    """Return all stored CV versions."""
    items = await service.list_cv()
    return CvListResponse(items=[CvResponse.model_validate(item) for item in items])


@router.get("/{cv_id}", response_model=CvResponse)
async def get_cv(
    cv_id: uuid.UUID,
    service: CvService = Depends(get_cv_service),
) -> CvResponse:
    """Return metadata for a single CV version."""
    cv = await service.get_cv(cv_id)
    return CvResponse.model_validate(cv)


@router.post("", response_model=CvResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    title: str = Form(...),
    file: UploadFile = File(...),
    notes: str | None = Form(default=None),
    is_current: bool = Form(default=False),
    service: CvService = Depends(get_cv_service),
) -> CvResponse:
    """Upload a PDF CV version."""
    body = await file.read()
    cv = await service.upload_cv(
        title=title,
        original_filename=file.filename or "cv.pdf",
        content_type=file.content_type,
        body=body,
        notes=notes,
        is_current=is_current,
    )
    return CvResponse.model_validate(cv)


@router.patch("/{cv_id}", response_model=CvResponse)
async def update_cv(
    cv_id: uuid.UUID,
    body: UpdateCvRequest,
    service: CvService = Depends(get_cv_service),
) -> CvResponse:
    """Update CV metadata."""
    cv = await service.update_cv(
        cv_id,
        **body.model_dump(exclude_unset=True),
    )
    return CvResponse.model_validate(cv)


@router.get("/{cv_id}/download")
async def download_cv(
    cv_id: uuid.UUID,
    service: CvService = Depends(get_cv_service),
) -> Response:
    """Stream a CV PDF as a file download."""
    cv, body = await service.get_cv_file(cv_id)
    return Response(
        content=body,
        media_type=cv.mime_type,
        headers={
            "Content-Disposition": build_attachment_content_disposition(
                cv.original_filename
            )
        },
    )


@router.get("/{cv_id}/file")
async def preview_cv(
    cv_id: uuid.UUID,
    service: CvService = Depends(get_cv_service),
) -> Response:
    """Stream a CV PDF for inline preview in the browser."""
    cv, body = await service.get_cv_file(cv_id)
    return Response(
        content=body,
        media_type=cv.mime_type,
        headers={
            "Content-Disposition": build_inline_content_disposition(
                cv.original_filename
            )
        },
    )


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(
    cv_id: uuid.UUID,
    service: CvService = Depends(get_cv_service),
) -> None:
    """Delete a CV version and its PDF from storage."""
    await service.delete_cv(cv_id)
