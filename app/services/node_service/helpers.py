import uuid
from typing import Any

from app.exceptions.node import (
    DuplicateNodeTitleError,
    InvalidNodeMoveError,
    InvalidReorderError,
    NodeHasContentError,
    NodeNotFoundError,
)
from app.models.node import Node
from app.repositories.node_repository import NodeRepository

UNSET: Any = object()


def normalize_content(content_md: str | None) -> str | None:
    if content_md is None:
        return None
    stripped = content_md.strip()
    return stripped or None


def ensure_unique_reorder_ids(ordered_ids: list[uuid.UUID]) -> None:
    if len(ordered_ids) != len(set(ordered_ids)):
        raise InvalidReorderError("Reorder payload contains duplicate node ids")


async def get_existing_parent(
    repository: NodeRepository,
    parent_id: uuid.UUID | None,
) -> Node | None:
    if parent_id is None:
        return None

    parent = await repository.get_by_id(parent_id)
    if parent is None:
        raise NodeNotFoundError(f"Parent node {parent_id} not found")
    return parent


async def ensure_parent_allows_children(
    repository: NodeRepository,
    parent_id: uuid.UUID,
) -> None:
    parent = await get_existing_parent(repository, parent_id)
    if parent is not None and parent.content_md is not None:
        raise NodeHasContentError("Parent node already stores an answer")


async def ensure_unique_sibling_title(
    repository: NodeRepository,
    parent_id: uuid.UUID | None,
    title: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if await repository.get_by_parent_and_title(
        parent_id,
        title,
        exclude_id=exclude_id,
    ):
        raise DuplicateNodeTitleError("A sibling with this title already exists")


async def load_reorder_nodes(
    repository: NodeRepository,
    ordered_ids: list[uuid.UUID],
) -> dict[uuid.UUID, Node]:
    nodes = await repository.get_by_ids(ordered_ids)
    node_map = {node.id: node for node in nodes}

    for node_id in ordered_ids:
        if node_id not in node_map:
            raise NodeNotFoundError(f"Node {node_id} not found")

    return node_map


async def validate_reorder(
    repository: NodeRepository,
    parent_id: uuid.UUID | None,
    ordered_ids: list[uuid.UUID],
    node_map: dict[uuid.UUID, Node],
    parent: Node | None,
) -> None:
    titles = [node_map[node_id].title for node_id in ordered_ids]
    if len(titles) != len(set(titles)):
        raise DuplicateNodeTitleError("A sibling with this title already exists")

    excluded_ids = set(ordered_ids)
    for sibling in await repository.list_children(parent_id):
        if sibling.id in excluded_ids:
            continue
        if sibling.title in titles:
            raise DuplicateNodeTitleError("A sibling with this title already exists")

    if parent is not None and parent.content_md is not None:
        for node_id in ordered_ids:
            if node_map[node_id].parent_id != parent_id:
                raise NodeHasContentError("Parent node already stores an answer")

    if parent_id is None:
        return

    for node_id in ordered_ids:
        if await repository.is_self_or_descendant(node_id, parent_id):
            raise InvalidNodeMoveError(
                "Cannot move a node into itself or its descendant"
            )


async def apply_reorder(
    repository: NodeRepository,
    parent_id: uuid.UUID | None,
    ordered_ids: list[uuid.UUID],
    node_map: dict[uuid.UUID, Node],
) -> None:
    for index, node_id in enumerate(ordered_ids):
        node = node_map[node_id]
        node.parent_id = parent_id
        node.sort_order = index
        await repository.save(node)


async def ensure_move_target_is_valid(
    repository: NodeRepository,
    node_id: uuid.UUID,
    parent_id: uuid.UUID | None,
) -> None:
    if parent_id is None:
        return

    if await repository.is_self_or_descendant(node_id, parent_id):
        raise InvalidNodeMoveError("Cannot move a node into itself or its descendant")

    await get_existing_parent(repository, parent_id)
