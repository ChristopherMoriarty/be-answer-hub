import uuid

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import API_PREFIX
from tests.factories import NodeFactory

NODES_URL = f"{API_PREFIX}/nodes"


async def _seed_tree(
    async_db_session: AsyncSession,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """Seed Backend -> Python -> Data types tree. Returns root, section, leaf ids."""
    root = NodeFactory(title="Backend", sort_order=0)
    async_db_session.add(root)
    await async_db_session.flush()

    section = NodeFactory(title="Python", parent_id=root.id, sort_order=0)
    async_db_session.add(section)
    await async_db_session.flush()

    leaf = NodeFactory(
        title="Data types",
        parent_id=section.id,
        sort_order=0,
        content_md="# int\n\nSigned integer type.",
    )
    async_db_session.add(leaf)
    await async_db_session.commit()

    return root.id, section.id, leaf.id


class TestNodesTree:
    async def test_get_empty_tree(self, client):
        response = await client.get(f"{NODES_URL}/tree")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"items": []}

    async def test_get_tree_with_nested_nodes(self, client, async_db_session):
        root_id, section_id, leaf_id = await _seed_tree(async_db_session)

        response = await client.get(f"{NODES_URL}/tree")

        assert response.status_code == status.HTTP_200_OK
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == str(root_id)
        assert items[0]["title"] == "Backend"
        assert items[0]["has_content"] is False

        python_node = items[0]["children"][0]
        assert python_node["id"] == str(section_id)
        assert python_node["has_content"] is False

        leaf_node = python_node["children"][0]
        assert leaf_node["id"] == str(leaf_id)
        assert leaf_node["title"] == "Data types"
        assert leaf_node["has_content"] is True
        assert leaf_node["children"] == []


class TestNodesGet:
    async def test_get_node_success(self, client, async_db_session):
        _, _, leaf_id = await _seed_tree(async_db_session)

        response = await client.get(f"{NODES_URL}/{leaf_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(leaf_id)
        assert data["title"] == "Data types"
        assert data["content_md"] == "# int\n\nSigned integer type."

    async def test_get_node_not_found(self, client):
        node_id = uuid.uuid4()
        response = await client.get(f"{NODES_URL}/{node_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == f"Node {node_id} not found"


class TestNodesCreate:
    async def test_create_root_section(self, client):
        response = await client.post(NODES_URL, json={"title": "Backend"})

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Backend"
        assert data["parent_id"] is None
        assert data["content_md"] is None
        assert data["sort_order"] == 0

    async def test_create_leaf_with_content(self, client, async_db_session):
        root = NodeFactory(title="Backend")
        async_db_session.add(root)
        await async_db_session.commit()

        response = await client.post(
            NODES_URL,
            json={
                "title": "Data types",
                "parent_id": str(root.id),
                "content_md": "# int",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["parent_id"] == str(root.id)
        assert data["content_md"] == "# int"
        assert data["sort_order"] == 0

    async def test_create_duplicate_sibling_title(self, client, async_db_session):
        root = NodeFactory(title="Backend")
        async_db_session.add(root)
        await async_db_session.commit()

        first = await client.post(
            NODES_URL,
            json={"title": "Python", "parent_id": str(root.id)},
        )
        assert first.status_code == status.HTTP_201_CREATED

        second = await client.post(
            NODES_URL,
            json={"title": "Python", "parent_id": str(root.id)},
        )
        assert second.status_code == status.HTTP_409_CONFLICT
        assert second.json()["detail"] == "A sibling with this title already exists"

    async def test_create_child_when_parent_has_content(self, client, async_db_session):
        leaf = NodeFactory(title="Data types", content_md="# int")
        async_db_session.add(leaf)
        await async_db_session.commit()

        response = await client.post(
            NODES_URL,
            json={"title": "Nested", "parent_id": str(leaf.id)},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Parent node already stores an answer"

    async def test_create_validation_error(self, client):
        response = await client.post(NODES_URL, json={"title": ""})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestNodesUpdate:
    async def test_update_title_and_content(self, client, async_db_session):
        _, _, leaf_id = await _seed_tree(async_db_session)

        response = await client.patch(
            f"{NODES_URL}/{leaf_id}",
            json={"title": "Data types updated", "content_md": "# updated"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Data types updated"
        assert data["content_md"] == "# updated"

    async def test_update_content_when_node_has_children(
        self, client, async_db_session
    ):
        root_id, section_id, _ = await _seed_tree(async_db_session)

        response = await client.patch(
            f"{NODES_URL}/{section_id}",
            json={"content_md": "# cannot add"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            response.json()["detail"]
            == "Cannot store an answer on a node with children"
        )

        get_response = await client.get(f"{NODES_URL}/{root_id}")
        assert get_response.status_code == status.HTTP_200_OK


class TestNodesReorder:
    async def test_reorder_root_siblings(self, client, async_db_session):
        backend = NodeFactory(title="Backend", sort_order=0)
        frontend = NodeFactory(title="Frontend", sort_order=1)
        async_db_session.add_all([backend, frontend])
        await async_db_session.commit()

        response = await client.put(
            f"{NODES_URL}/reorder",
            json={
                "parent_id": None,
                "ordered_ids": [str(frontend.id), str(backend.id)],
            },
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        tree_response = await client.get(f"{NODES_URL}/tree")
        titles = [item["title"] for item in tree_response.json()["items"]]
        assert titles == ["Frontend", "Backend"]

    async def test_reorder_moves_node_into_parent(self, client, async_db_session):
        backend = NodeFactory(title="Backend", sort_order=0)
        frontend = NodeFactory(title="Frontend", sort_order=1)
        async_db_session.add_all([backend, frontend])
        await async_db_session.flush()

        python = NodeFactory(title="Python", parent_id=backend.id, sort_order=0)
        async_db_session.add(python)
        await async_db_session.commit()

        response = await client.put(
            f"{NODES_URL}/reorder",
            json={
                "parent_id": str(frontend.id),
                "ordered_ids": [str(python.id)],
            },
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        tree_response = await client.get(f"{NODES_URL}/tree")
        items = tree_response.json()["items"]
        frontend_node = next(item for item in items if item["id"] == str(frontend.id))
        assert [child["title"] for child in frontend_node["children"]] == ["Python"]

    async def test_reorder_duplicate_ids(self, client, async_db_session):
        backend = NodeFactory(title="Backend")
        async_db_session.add(backend)
        await async_db_session.commit()

        response = await client.put(
            f"{NODES_URL}/reorder",
            json={"parent_id": None, "ordered_ids": [str(backend.id), str(backend.id)]},
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_reorder_move_into_descendant(self, client, async_db_session):
        root_id, section_id, _ = await _seed_tree(async_db_session)

        response = await client.put(
            f"{NODES_URL}/reorder",
            json={
                "parent_id": str(section_id),
                "ordered_ids": [str(root_id)],
            },
        )

        assert response.status_code == status.HTTP_409_CONFLICT


class TestNodesMove:
    async def test_move_node_to_root(self, client, async_db_session):
        root_id, section_id, _ = await _seed_tree(async_db_session)

        response = await client.patch(
            f"{NODES_URL}/{section_id}/move",
            json={"parent_id": None},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(section_id)
        assert data["parent_id"] is None
        assert data["sort_order"] == 1

        tree_response = await client.get(f"{NODES_URL}/tree")
        root_titles = {item["title"] for item in tree_response.json()["items"]}
        assert root_titles == {"Backend", "Python"}

        backend = next(
            item for item in tree_response.json()["items"] if item["id"] == str(root_id)
        )
        assert backend["children"] == []

    async def test_move_node_into_descendant(self, client, async_db_session):
        root_id, section_id, _ = await _seed_tree(async_db_session)

        response = await client.patch(
            f"{NODES_URL}/{root_id}/move",
            json={"parent_id": str(section_id)},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            response.json()["detail"]
            == "Cannot move a node into itself or its descendant"
        )


class TestNodesDelete:
    async def test_delete_node_cascades_children(self, client, async_db_session):
        root_id, _, _ = await _seed_tree(async_db_session)

        response = await client.delete(f"{NODES_URL}/{root_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        tree_response = await client.get(f"{NODES_URL}/tree")
        assert tree_response.json()["items"] == []

    async def test_delete_node_not_found(self, client):
        response = await client.delete(f"{NODES_URL}/{uuid.uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
