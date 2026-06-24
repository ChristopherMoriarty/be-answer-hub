import uuid
from unittest.mock import MagicMock

from fastapi import status

from app.core.constants import API_PREFIX
from tests.factories import CvFactory

CV_URL = f"{API_PREFIX}/cv"
PDF_BYTES = b"%PDF-1.4 test content"


def _pdf_file(
    *,
    filename: str = "resume.pdf",
    content: bytes = PDF_BYTES,
    content_type: str = "application/pdf",
) -> dict[str, tuple[str, bytes, str]]:
    return {"file": (filename, content, content_type)}


class TestCvList:
    async def test_list_empty(self, client):
        response = await client.get(CV_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"items": []}

    async def test_list_returns_newest_first(self, client, async_db_session):
        older = CvFactory(title="Older")
        async_db_session.add(older)
        await async_db_session.commit()

        newer = CvFactory(title="Newer")
        async_db_session.add(newer)
        await async_db_session.commit()

        response = await client.get(CV_URL)

        assert response.status_code == status.HTTP_200_OK
        titles = [item["title"] for item in response.json()["items"]]
        assert titles == ["Newer", "Older"]


class TestCvUpload:
    async def test_upload_cv(self, client, mock_minio_client: MagicMock):
        response = await client.post(
            CV_URL,
            data={"title": "Backend v3", "notes": "For FAANG"},
            files=_pdf_file(),
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Backend v3"
        assert data["original_filename"] == "resume.pdf"
        assert data["file_size"] == len(PDF_BYTES)
        assert data["mime_type"] == "application/pdf"
        assert data["notes"] == "For FAANG"
        assert data["is_current"] is False

        mock_minio_client.put_object.assert_awaited_once()
        call = mock_minio_client.put_object.await_args
        assert call.args[0].startswith("cv/")
        assert call.args[0].endswith(".pdf")
        assert call.kwargs["content_type"] == "application/pdf"

    async def test_upload_rejects_non_pdf(self, client, mock_minio_client: MagicMock):
        response = await client.post(
            CV_URL,
            data={"title": "Not a PDF"},
            files=_pdf_file(
                filename="notes.txt",
                content=b"hello",
                content_type="text/plain",
            ),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == "Only PDF files are allowed"
        mock_minio_client.put_object.assert_not_awaited()

    async def test_upload_rejects_empty_file(
        self, client, mock_minio_client: MagicMock
    ):
        response = await client.post(
            CV_URL,
            data={"title": "Empty"},
            files=_pdf_file(content=b""),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == "Uploaded file is empty"
        mock_minio_client.put_object.assert_not_awaited()


class TestCvGet:
    async def test_get_cv(self, client, async_db_session):
        cv = CvFactory(title="Backend v2", notes="Updated intro")
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.get(f"{CV_URL}/{cv.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(cv.id)
        assert data["title"] == "Backend v2"
        assert data["notes"] == "Updated intro"

    async def test_get_cv_not_found(self, client):
        response = await client.get(f"{CV_URL}/{uuid.uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCvUpdate:
    async def test_update_cv_metadata(self, client, async_db_session):
        cv = CvFactory(title="Old title")
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.patch(
            f"{CV_URL}/{cv.id}",
            json={"title": "New title", "notes": "Fresh notes"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New title"
        assert data["notes"] == "Fresh notes"

    async def test_set_current_unsets_other_versions(
        self,
        client,
        async_db_session,
        mock_minio_client: MagicMock,
    ):
        first = CvFactory(title="First", is_current=True)
        async_db_session.add(first)
        await async_db_session.commit()

        response = await client.post(
            CV_URL,
            data={"title": "Second", "is_current": "true"},
            files=_pdf_file(filename="second.pdf"),
        )

        assert response.status_code == status.HTTP_201_CREATED
        second_id = response.json()["id"]

        list_response = await client.get(CV_URL)
        items = {
            item["id"]: item["is_current"] for item in list_response.json()["items"]
        }

        assert items[str(first.id)] is False
        assert items[second_id] is True
        mock_minio_client.put_object.assert_awaited_once()

    async def test_unset_current(self, client, async_db_session):
        cv = CvFactory(title="Current CV", is_current=False)
        async_db_session.add(cv)
        await async_db_session.commit()

        set_response = await client.patch(
            f"{CV_URL}/{cv.id}",
            json={"is_current": True},
        )
        assert set_response.status_code == status.HTTP_200_OK
        assert set_response.json()["is_current"] is True

        response = await client.patch(
            f"{CV_URL}/{cv.id}",
            json={"is_current": False},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_current"] is False

        list_response = await client.get(CV_URL)
        assert all(not item["is_current"] for item in list_response.json()["items"])


class TestCvDownload:
    async def test_download_streams_pdf(
        self,
        client,
        async_db_session,
        mock_minio_client: MagicMock,
    ):
        cv = CvFactory(original_filename="resume.pdf")
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.get(f"{CV_URL}/{cv.id}/download")

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b"%PDF-1.4 preview"
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"].startswith(
            'attachment; filename="resume.pdf"'
        )
        mock_minio_client.get_object.assert_awaited_once_with(cv.storage_key)

    async def test_download_handles_non_ascii_filename(
        self,
        client,
        async_db_session,
        mock_minio_client: MagicMock,
    ):
        cv = CvFactory(original_filename="Резюме Backend.pdf")
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.get(f"{CV_URL}/{cv.id}/download")

        assert response.status_code == status.HTTP_200_OK
        assert "attachment;" in response.headers["content-disposition"]
        assert "filename*=UTF-8''" in response.headers["content-disposition"]
        assert 'filename="Backend.pdf"' in response.headers["content-disposition"]
        mock_minio_client.get_object.assert_awaited_once_with(cv.storage_key)


class TestCvPreview:
    async def test_preview_streams_pdf(
        self,
        client,
        async_db_session,
        mock_minio_client: MagicMock,
    ):
        cv = CvFactory(original_filename="resume.pdf")
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.get(f"{CV_URL}/{cv.id}/file")

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b"%PDF-1.4 preview"
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"].startswith(
            'inline; filename="resume.pdf"'
        )
        mock_minio_client.get_object.assert_awaited_once_with(cv.storage_key)

    async def test_preview_handles_non_ascii_filename(
        self,
        client,
        async_db_session,
        mock_minio_client: MagicMock,
    ):
        cv = CvFactory(original_filename="Резюме Backend.pdf")
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.get(f"{CV_URL}/{cv.id}/file")

        assert response.status_code == status.HTTP_200_OK
        assert "filename*=UTF-8''" in response.headers["content-disposition"]
        assert 'filename="Backend.pdf"' in response.headers["content-disposition"]
        mock_minio_client.get_object.assert_awaited_once_with(cv.storage_key)


class TestCvDelete:
    async def test_delete_cv(
        self, client, async_db_session, mock_minio_client: MagicMock
    ):
        cv = CvFactory()
        async_db_session.add(cv)
        await async_db_session.commit()

        response = await client.delete(f"{CV_URL}/{cv.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_minio_client.delete_object.assert_awaited_once_with(cv.storage_key)

        list_response = await client.get(CV_URL)
        assert list_response.json()["items"] == []

    async def test_delete_cv_not_found(self, client):
        response = await client.delete(f"{CV_URL}/{uuid.uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
