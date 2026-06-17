import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.node import (
    DuplicateNodeTitleError,
    InvalidNodeMoveError,
    NodeHasContentError,
    NodeNotFoundError,
)
from app.models.node import Node
from app.repositories.node_repository import NodeRepository

_UNSET: Any = object()


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
        normalized_content = self._normalize_content(content_md)

        if parent_id is not None:
            parent = await self._repository.get_by_id(parent_id)
            if parent is None:
                raise NodeNotFoundError(f"Parent node {parent_id} not found")
            if parent.content_md is not None:
                raise NodeHasContentError("Parent node already stores an answer")

        if await self._repository.get_by_parent_and_title(parent_id, title):
            raise DuplicateNodeTitleError("A sibling with this title already exists")

        resolved_sort_order = (
            sort_order
            if sort_order is not None
            else await self._repository.get_max_sort_order(parent_id) + 1
        )

        node = await self._repository.create(
            title=title,
            parent_id=parent_id,
            content_md=normalized_content,
            sort_order=resolved_sort_order,
        )
        await self._session.commit()
        return node

    async def update_node(
        self,
        node_id: uuid.UUID,
        *,
        title: str | Any = _UNSET,
        content_md: str | None | Any = _UNSET,
        sort_order: int | Any = _UNSET,
    ) -> Node:
        """Update only the fields explicitly provided by the caller."""
        node = await self.get_node(node_id)

        if title is not _UNSET:
            if await self._repository.get_by_parent_and_title(
                node.parent_id,
                title,
                exclude_id=node_id,
            ):
                raise DuplicateNodeTitleError(
                    "A sibling with this title already exists"
                )
            node.title = title

        if content_md is not _UNSET:
            if await self._repository.has_children(node_id):
                raise NodeHasContentError(
                    "Cannot store an answer on a node with children"
                )
            node.content_md = self._normalize_content(content_md)

        if sort_order is not _UNSET:
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

        if parent_id is not None:
            if await self._repository.is_self_or_descendant(node_id, parent_id):
                raise InvalidNodeMoveError(
                    "Cannot move a node into itself or its descendant"
                )

            parent = await self._repository.get_by_id(parent_id)
            if parent is None:
                raise NodeNotFoundError(f"Parent node {parent_id} not found")

        if await self._repository.get_by_parent_and_title(
            parent_id, node.title, exclude_id=node_id
        ):
            raise DuplicateNodeTitleError("A sibling with this title already exists")

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

    async def delete_node(self, node_id: uuid.UUID) -> None:
        """Delete a node and all nested descendants."""
        node = await self.get_node(node_id)
        await self._repository.delete(node)
        await self._session.commit()

    @staticmethod
    def _normalize_content(content_md: str | None) -> str | None:
        if content_md is None:
            return None
        stripped = content_md.strip()
        return stripped or None
