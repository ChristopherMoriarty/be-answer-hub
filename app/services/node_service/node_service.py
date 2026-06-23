import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.node import NodeHasContentError, NodeNotFoundError
from app.models.node import Node
from app.repositories.node_repository import NodeRepository

from .helpers import (
    UNSET,
    apply_reorder,
    ensure_move_target_is_valid,
    ensure_parent_allows_children,
    ensure_unique_reorder_ids,
    ensure_unique_sibling_title,
    get_existing_parent,
    load_reorder_nodes,
    normalize_content,
    validate_reorder,
)


class NodeService:
    """Business logic for hierarchical topic nodes."""

    def __init__(self, session: AsyncSession, repository: NodeRepository) -> None:
        self._session = session
        self._repository = repository

    async def list_nodes(self) -> list[Node]:
        """Return all nodes for tree construction."""
        return await self._repository.list_all()

    async def get_node(self, node_id: uuid.UUID) -> Node:
        """Return a node or raise if it does not exist."""
        node = await self._repository.get_by_id(node_id)
        if node is None:
            raise NodeNotFoundError(f"Node {node_id} not found")
        return node

    async def create_node(
        self,
        *,
        title: str,
        parent_id: uuid.UUID | None = None,
        content_md: str | None = None,
        sort_order: int | None = None,
    ) -> Node:
        """Create a section or a leaf node with markdown content."""
        if parent_id is not None:
            await ensure_parent_allows_children(self._repository, parent_id)

        await ensure_unique_sibling_title(self._repository, parent_id, title)

        resolved_sort_order = (
            sort_order
            if sort_order is not None
            else await self._repository.get_max_sort_order(parent_id) + 1
        )

        node = await self._repository.create(
            title=title,
            parent_id=parent_id,
            content_md=normalize_content(content_md),
            sort_order=resolved_sort_order,
        )
        await self._session.commit()
        return node

    async def update_node(
        self,
        node_id: uuid.UUID,
        *,
        title: str | Any = UNSET,
        content_md: str | None | Any = UNSET,
        sort_order: int | Any = UNSET,
    ) -> Node:
        """Update only the fields explicitly provided by the caller."""
        node = await self.get_node(node_id)

        if title is not UNSET:
            await ensure_unique_sibling_title(
                self._repository,
                node.parent_id,
                title,
                exclude_id=node_id,
            )
            node.title = title

        if content_md is not UNSET:
            if await self._repository.has_children(node_id):
                raise NodeHasContentError(
                    "Cannot store an answer on a node with children"
                )
            node.content_md = normalize_content(content_md)

        if sort_order is not UNSET:
            node.sort_order = sort_order

        node = await self._repository.save(node)
        await self._session.commit()
        return node

    async def move_node(
        self,
        node_id: uuid.UUID,
        *,
        parent_id: uuid.UUID | None,
        sort_order: int | None = None,
    ) -> Node:
        """Move a node under another parent or to the root level."""
        node = await self.get_node(node_id)

        await ensure_move_target_is_valid(self._repository, node_id, parent_id)
        await ensure_unique_sibling_title(
            self._repository,
            parent_id,
            node.title,
            exclude_id=node_id,
        )

        resolved_sort_order = (
            sort_order
            if sort_order is not None
            else await self._repository.get_max_sort_order(parent_id) + 1
        )

        node.parent_id = parent_id
        node.sort_order = resolved_sort_order
        node = await self._repository.save(node)
        await self._session.commit()
        return node

    async def reorder_nodes(
        self,
        *,
        parent_id: uuid.UUID | None,
        ordered_ids: list[uuid.UUID],
    ) -> None:
        """Assign sibling order and optionally move nodes under a parent."""
        ensure_unique_reorder_ids(ordered_ids)
        parent = await get_existing_parent(self._repository, parent_id)
        node_map = await load_reorder_nodes(self._repository, ordered_ids)
        await validate_reorder(
            self._repository,
            parent_id,
            ordered_ids,
            node_map,
            parent,
        )
        await apply_reorder(self._repository, parent_id, ordered_ids, node_map)
        await self._session.commit()

    async def delete_node(self, node_id: uuid.UUID) -> None:
        """Delete a node and all nested descendants."""
        node = await self.get_node(node_id)
        await self._repository.delete(node)
        await self._session.commit()
