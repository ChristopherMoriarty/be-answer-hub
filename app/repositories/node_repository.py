import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.models.node import Node
from app.models.node_translation import NodeTranslation


class NodeRepository:
    """Data access layer for hierarchical topic nodes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, node_id: uuid.UUID) -> Node | None:
        """Return a node by primary key with translations loaded."""
        stmt = (
            select(Node)
            .where(Node.id == node_id)
            .options(selectinload(Node.translations))
            .execution_options(populate_existing=True)
        )
        return await self._session.scalar(stmt)

    async def list_all(self) -> list[Node]:
        """Return all nodes ordered for tree construction."""
        stmt = (
            select(Node)
            .options(selectinload(Node.translations))
            .order_by(Node.parent_id.nulls_first(), Node.sort_order, Node.title)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_ids(self, node_ids: list[uuid.UUID]) -> list[Node]:
        """Return nodes for the given primary keys."""
        if not node_ids:
            return []

        stmt = (
            select(Node)
            .where(Node.id.in_(node_ids))
            .options(selectinload(Node.translations))
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def list_children(self, parent_id: uuid.UUID | None) -> list[Node]:
        """Return direct children of a parent ordered for display."""
        parent_filter = (
            Node.parent_id.is_(None)
            if parent_id is None
            else Node.parent_id == parent_id
        )
        stmt = (
            select(Node)
            .where(parent_filter)
            .options(selectinload(Node.translations))
            .order_by(Node.sort_order, Node.title)
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

    async def has_translations(self, node_id: uuid.UUID) -> bool:
        """Return True if the node has at least one translation."""
        stmt = select(exists().where(NodeTranslation.node_id == node_id))
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
        sort_order: int = 0,
    ) -> Node:
        """Persist a new node."""
        node = Node(
            title=title,
            parent_id=parent_id,
            sort_order=sort_order,
        )
        self._session.add(node)
        await self._session.flush()
        return node

    async def upsert_translation(
        self,
        *,
        node_id: uuid.UUID,
        language: str,
        content_md: str,
    ) -> NodeTranslation:
        """Create or update a translation for a node language."""
        stmt = select(NodeTranslation).where(
            NodeTranslation.node_id == node_id,
            NodeTranslation.language == language,
        )
        translation = await self._session.scalar(stmt)
        if translation is None:
            translation = NodeTranslation(
                node_id=node_id,
                language=language,
                content_md=content_md,
            )
            self._session.add(translation)
        else:
            translation.content_md = content_md
            self._session.add(translation)

        await self._session.flush()
        await self._session.refresh(translation)
        return translation

    async def get_translation(
        self, node_id: uuid.UUID, language: str
    ) -> NodeTranslation | None:
        stmt = select(NodeTranslation).where(
            NodeTranslation.node_id == node_id,
            NodeTranslation.language == language,
        )
        return await self._session.scalar(stmt)

    async def delete_translation(self, translation: NodeTranslation) -> None:
        await self._session.delete(translation)
        await self._session.flush()

    async def save(self, node: Node) -> Node:
        """Flush pending changes for an existing node."""
        self._session.add(node)
        await self._session.flush()
        return node

    async def delete(self, node: Node) -> None:
        """Delete a node. Child nodes are removed by DB cascade."""
        await self._session.delete(node)
        await self._session.flush()
