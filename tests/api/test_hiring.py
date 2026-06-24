import uuid

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import API_PREFIX, STEP_KIND_LABELS
from tests.factories import (
    HiringBoardColumnFactory,
    HiringBoardFactory,
    HiringProcessFactory,
)

HIRING_URL = f"{API_PREFIX}/hiring"


async def _create_board(client, *, title: str = "Python") -> dict:
    response = await client.post(f"{HIRING_URL}/boards", json={"title": title})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


async def _add_column(
    client,
    board_id: str,
    *,
    step_kind: str,
    custom_title: str | None = None,
) -> dict:
    payload: dict[str, str] = {"step_kind": step_kind}
    if custom_title is not None:
        payload["custom_title"] = custom_title
    response = await client.post(
        f"{HIRING_URL}/boards/{board_id}/columns",
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def _create_process(
    client,
    board_id: str,
    *,
    company: str = "Acme",
    source: str = "LinkedIn",
    result: str = "in_progress",
    offer_details: str | None = None,
    notes: str | None = None,
) -> dict:
    payload: dict[str, str | None] = {
        "company": company,
        "source": source,
        "result": result,
        "notes": notes,
    }
    if offer_details is not None:
        payload["offer_details"] = offer_details
    response = await client.post(
        f"{HIRING_URL}/boards/{board_id}/processes",
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


class TestHiringBoardsList:
    async def test_list_empty(self, client):
        response = await client.get(f"{HIRING_URL}/boards")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"items": []}

    async def test_list_boards(self, client, async_db_session: AsyncSession):
        first = HiringBoardFactory(title="Python", sort_order=0)
        second = HiringBoardFactory(title="Go", sort_order=1)
        async_db_session.add_all([first, second])
        await async_db_session.commit()

        response = await client.get(f"{HIRING_URL}/boards")

        assert response.status_code == status.HTTP_200_OK
        titles = [item["title"] for item in response.json()["items"]]
        assert titles == ["Python", "Go"]


class TestHiringBoardsCrud:
    async def test_create_board(self, client):
        data = await _create_board(client, title="Python")

        assert data["title"] == "Python"
        assert len(data["columns"]) == 3
        assert [column["title"] for column in data["columns"]] == [
            "Applied",
            "Screening",
            "Technical interview",
        ]
        assert data["processes"] == []
        assert data["step_kinds"] == STEP_KIND_LABELS

    async def test_get_board(self, client):
        created = await _create_board(client, title="Backend")
        board_id = created["id"]

        response = await client.get(f"{HIRING_URL}/boards/{board_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Backend"
        assert [column["title"] for column in data["columns"]] == [
            "Applied",
            "Screening",
            "Technical interview",
        ]

    async def test_get_board_backfills_missing_default_columns(
        self, client, async_db_session
    ):
        board = HiringBoardFactory(title="Legacy")
        column = HiringBoardColumnFactory(
            board=board, step_kind="applied", sort_order=0
        )
        async_db_session.add_all([board, column])
        await async_db_session.commit()

        response = await client.get(f"{HIRING_URL}/boards/{board.id}")

        assert response.status_code == status.HTTP_200_OK
        titles = [column["title"] for column in response.json()["columns"]]
        assert titles == ["Applied", "Screening", "Technical interview"]

    async def test_get_board_not_found(self, client):
        board_id = uuid.uuid4()
        response = await client.get(f"{HIRING_URL}/boards/{board_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == f"Hiring board {board_id} not found"

    async def test_update_board(self, client):
        created = await _create_board(client, title="Old title")
        board_id = created["id"]

        response = await client.patch(
            f"{HIRING_URL}/boards/{board_id}",
            json={"title": "New title"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "New title"

    async def test_delete_board(self, client):
        created = await _create_board(client)
        board_id = created["id"]

        response = await client.delete(f"{HIRING_URL}/boards/{board_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        list_response = await client.get(f"{HIRING_URL}/boards")
        assert list_response.json()["items"] == []


class TestHiringColumns:
    async def test_add_preset_column(self, client):
        board = await _create_board(client)
        data = await _add_column(client, board["id"], step_kind="final")

        assert len(data["columns"]) == 4
        column = next(item for item in data["columns"] if item["step_kind"] == "final")
        assert column["title"] == "Final round"

    async def test_add_custom_column(self, client):
        board = await _create_board(client)
        data = await _add_column(
            client,
            board["id"],
            step_kind="custom",
            custom_title="Take-home",
        )

        column = next(item for item in data["columns"] if item["step_kind"] == "custom")
        assert column["title"] == "Take-home"
        assert column["custom_title"] == "Take-home"

    async def test_add_column_rejects_unknown_step_kind(self, client):
        board = await _create_board(client)

        response = await client.post(
            f"{HIRING_URL}/boards/{board['id']}/columns",
            json={"step_kind": "recruiter"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == "Unknown step kind: recruiter"

    async def test_add_custom_column_requires_title(self, client):
        board = await _create_board(client)

        response = await client.post(
            f"{HIRING_URL}/boards/{board['id']}/columns",
            json={"step_kind": "custom"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == "Custom step requires a title"

    async def test_delete_column(self, client):
        board = await _create_board(client)
        column_id = next(
            column["id"]
            for column in board["columns"]
            if column["step_kind"] == "applied"
        )

        response = await client.delete(
            f"{HIRING_URL}/boards/{board['id']}/columns/{column_id}",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["columns"]) == 2
        titles = [column["title"] for column in response.json()["columns"]]
        assert titles == ["Screening", "Technical interview"]

    async def test_delete_column_not_found(self, client):
        board = await _create_board(client)
        column_id = uuid.uuid4()

        response = await client.delete(
            f"{HIRING_URL}/boards/{board['id']}/columns/{column_id}",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == f"Column {column_id} not found"

    async def test_reorder_columns(self, client):
        board = await _create_board(client)
        by_kind = {column["step_kind"]: column["id"] for column in board["columns"]}

        response = await client.put(
            f"{HIRING_URL}/boards/{board['id']}/columns/reorder",
            json={
                "ordered_ids": [
                    by_kind["technical"],
                    by_kind["hr_screen"],
                    by_kind["applied"],
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK
        titles = [column["title"] for column in response.json()["columns"]]
        assert titles == ["Technical interview", "Screening", "Applied"]

    async def test_reorder_columns_rejects_unknown_id(self, client):
        board = await _create_board(client)
        column_id = board["columns"][0]["id"]
        unknown_id = str(uuid.uuid4())

        response = await client.put(
            f"{HIRING_URL}/boards/{board['id']}/columns/reorder",
            json={"ordered_ids": [unknown_id, column_id]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == (
            "Reorder payload must include all board columns exactly once"
        )


class TestHiringProcesses:
    async def test_create_process(self, client):
        board = await _create_board(client)
        data = await _create_process(
            client,
            board["id"],
            company="Acme",
            source="Referral",
            notes="Warm intro",
        )

        assert len(data["processes"]) == 1
        process = data["processes"][0]
        assert process["company"] == "Acme"
        assert process["source"] == "Referral"
        assert process["result"] == "in_progress"
        assert process["notes"] == "Warm intro"
        assert process["offer_details"] is None
        assert process["cells"] == []

    async def test_create_process_clears_offer_details_when_not_offer(self, client):
        board = await _create_board(client)

        response = await client.post(
            f"{HIRING_URL}/boards/{board['id']}/processes",
            json={
                "company": "Acme",
                "result": "in_progress",
                "offer_details": "$150k",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        process = response.json()["processes"][0]
        assert process["offer_details"] is None

    async def test_update_process(self, client):
        board = await _create_board(client)
        with_process = await _create_process(client, board["id"], company="Acme")
        process_id = with_process["processes"][0]["id"]

        response = await client.patch(
            f"{HIRING_URL}/processes/{process_id}",
            json={
                "company": "Globex",
                "result": "offer",
                "offer_details": "$180k base",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["company"] == "Globex"
        assert data["result"] == "offer"
        assert data["offer_details"] == "$180k base"

    async def test_update_process_clears_offer_details_when_result_changes(
        self,
        client,
    ):
        board = await _create_board(client)
        with_process = await _create_process(
            client,
            board["id"],
            company="Acme",
            result="offer",
            offer_details="$150k",
        )
        process_id = with_process["processes"][0]["id"]

        response = await client.patch(
            f"{HIRING_URL}/processes/{process_id}",
            json={"result": "rejected"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["result"] == "rejected"
        assert response.json()["offer_details"] is None

    async def test_update_process_not_found(self, client):
        process_id = uuid.uuid4()
        response = await client.patch(
            f"{HIRING_URL}/processes/{process_id}",
            json={"company": "Acme"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == f"Process {process_id} not found"

    async def test_delete_process(self, client):
        board = await _create_board(client)
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]

        response = await client.delete(f"{HIRING_URL}/processes/{process_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        board_response = await client.get(f"{HIRING_URL}/boards/{board['id']}")
        assert board_response.json()["processes"] == []


class TestHiringStepValues:
    async def test_upsert_step_value_creates_cell(self, client):
        board = await _create_board(client)
        with_column = await _add_column(client, board["id"], step_kind="hr_screen")
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]
        column_id = with_column["columns"][0]["id"]

        response = await client.put(
            f"{HIRING_URL}/processes/{process_id}/cells/{column_id}",
            json={"status": "scheduled", "event_date": "2025-06-10"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["column_id"] == column_id
        assert data["status"] == "scheduled"
        assert data["event_date"] == "2025-06-10"

        board_response = await client.get(f"{HIRING_URL}/boards/{board['id']}")
        cells = board_response.json()["processes"][0]["cells"]
        assert len(cells) == 1
        assert cells[0]["status"] == "scheduled"

    async def test_upsert_step_value_updates_existing_cell(self, client):
        board = await _create_board(client)
        with_column = await _add_column(client, board["id"], step_kind="technical")
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]
        column_id = with_column["columns"][0]["id"]
        url = f"{HIRING_URL}/processes/{process_id}/cells/{column_id}"

        first = await client.put(url, json={"status": "scheduled"})
        assert first.status_code == status.HTTP_200_OK

        second = await client.put(
            url,
            json={"status": "passed", "event_date": "2025-06-12"},
        )

        assert second.status_code == status.HTTP_200_OK
        assert second.json()["status"] == "passed"
        assert second.json()["event_date"] == "2025-06-12"

    async def test_failed_step_sets_result_to_rejected(self, client):
        board = await _create_board(client)
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]
        technical_id = next(
            column["id"]
            for column in board["columns"]
            if column["step_kind"] == "technical"
        )

        response = await client.put(
            f"{HIRING_URL}/processes/{process_id}/cells/{technical_id}",
            json={"status": "failed", "event_date": "2025-06-15"},
        )

        assert response.status_code == status.HTTP_200_OK

        board_response = await client.get(f"{HIRING_URL}/boards/{board['id']}")
        process = board_response.json()["processes"][0]
        assert process["result"] == "rejected"
        assert process["offer_details"] is None

    async def test_failed_on_applied_does_not_reject(self, client):
        board = await _create_board(client)
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]
        applied_id = next(
            column["id"]
            for column in board["columns"]
            if column["step_kind"] == "applied"
        )

        response = await client.put(
            f"{HIRING_URL}/processes/{process_id}/cells/{applied_id}",
            json={"status": "failed"},
        )

        assert response.status_code == status.HTTP_200_OK

        board_response = await client.get(f"{HIRING_URL}/boards/{board['id']}")
        assert board_response.json()["processes"][0]["result"] == "in_progress"

    async def test_upsert_step_value_rejects_unknown_status(self, client):
        board = await _create_board(client)
        with_column = await _add_column(client, board["id"], step_kind="applied")
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]
        column_id = with_column["columns"][0]["id"]

        response = await client.put(
            f"{HIRING_URL}/processes/{process_id}/cells/{column_id}",
            json={"status": "maybe"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == "Unknown step status: maybe"

    async def test_upsert_step_value_rejects_foreign_column(
        self,
        client,
        async_db_session: AsyncSession,
    ):
        board = await _create_board(client)
        other_board = HiringBoardFactory(title="Other")
        other_column = HiringBoardColumnFactory(
            board=other_board,
            step_kind="applied",
        )
        async_db_session.add_all([other_board, other_column])
        await async_db_session.commit()
        with_process = await _create_process(client, board["id"])
        process_id = with_process["processes"][0]["id"]

        response = await client.put(
            f"{HIRING_URL}/processes/{process_id}/cells/{other_column.id}",
            json={"status": "passed"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == f"Column {other_column.id} not found"

    async def test_upsert_step_value_process_not_found(self, client):
        board = await _create_board(client)
        with_column = await _add_column(client, board["id"], step_kind="applied")
        column_id = with_column["columns"][0]["id"]
        process_id = uuid.uuid4()

        response = await client.put(
            f"{HIRING_URL}/processes/{process_id}/cells/{column_id}",
            json={"status": "passed"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == f"Process {process_id} not found"


class TestHiringBoardDetail:
    async def test_board_detail_includes_columns_processes_and_cells(
        self,
        client,
        async_db_session: AsyncSession,
    ):
        board = HiringBoardFactory(title="Python")
        column = HiringBoardColumnFactory(
            board=board,
            step_kind="technical",
            sort_order=0,
        )
        process = HiringProcessFactory(
            board=board,
            company="Acme",
            source="LinkedIn",
            sort_order=0,
        )
        async_db_session.add_all([board, column, process])
        await async_db_session.commit()

        response = await client.get(f"{HIRING_URL}/boards/{board.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Python"
        assert len(data["columns"]) == 1
        assert data["columns"][0]["title"] == "Technical interview"
        assert len(data["processes"]) == 1
        assert data["processes"][0]["company"] == "Acme"
