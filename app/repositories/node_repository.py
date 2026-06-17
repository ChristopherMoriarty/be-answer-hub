import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.node import Node


class NodeRepository:
    """Data access layer for hierarchical topic nodes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, node_id: uuid.UUID) -> Node | None:
        """Return a node by primary key."""
        return await self._session.get(Node, node_id)

    async def list_all(self) -> list[Node]:
        """Return all nodes ordered for tree construction."""
        stmt = select(Node).order_by(
            Node.parent_id.nulls_first(), Node.sort_order, Node.title
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_parent_and_title(
        self,
        parent_id: uuid.UUID | None,
        title: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> Node | None:
        """Return a sibling node with the same title, if it exists."""
        stmt = select(Node).where(
            Node.parent_id.is_(None)
            if parent_id is None
            else Node.parent_id == parent_id,
            Node.title == title,
        )
        if exclude_id is not None:
            stmt = stmt.where(Node.id != exclude_id)

        return await self._session.scalar(stmt)

    async def has_children(self, node_id: uuid.UUID) -> bool:
        """Return True if the node has at least one child."""
        stmt = select(exists().where(Node.parent_id == node_id))
        return bool(await self._session.scalar(stmt))

    async def is_self_or_descendant(
        self, ancestor_id: uuid.UUID, node_id: uuid.UUID
    ) -> bool:
        """Return True if node_id is ancestor_id or nested under it."""
        if ancestor_id == node_id:
            return True

        tree = (
            select(Node.id.label("id"))
            .where(Node.id == ancestor_id)
            .cte(name="tree", recursive=True)
        )
        tree_alias = aliased(tree)
        tree = tree.union_all(
            select(Node.id).where(Node.parent_id == tree_alias.c.id),
        )

        stmt = select(exists().select_from(tree).where(tree.c.id == node_id))
        return bool(await self._session.scalar(stmt))

    async def get_max_sort_order(self, parent_id: uuid.UUID | None) -> int:
        """Return the highest sort_order among siblings, or -1 if there are none."""
        parent_filter = (
            Node.parent_id.is_(None)
            if parent_id is None
            else Node.parent_id == parent_id
        )
        stmt = select(func.coalesce(func.max(Node.sort_order), -1)).where(parent_filter)
        result = await self._session.scalar(stmt)
        return -1 if result is None else int(result)

    async def create(
        self,
        *,
        title: str,
        parent_id: uuid.UUID | None = None,
        content_md: str | None = None,
        sort_order: int = 0,
    ) -> Node:
        """Persist a new node."""
        node = Node(
            title=title,
            parent_id=parent_id,
            content_md=content_md,
            sort_order=sort_order,
        )
        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def save(self, node: Node) -> Node:
        """Flush pending changes for an existing node."""
        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def delete(self, node: Node) -> None:
        """Delete a node. Child nodes are removed by DB cascade."""
        await self._session.delete(node)
        await self._session.flush()
