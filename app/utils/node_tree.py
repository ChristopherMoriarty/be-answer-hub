import uuid
from collections import defaultdict

from app.models.node import Node
from app.schemas.responses.node import NodeTreeItem


def build_node_tree(nodes: list[Node]) -> list[NodeTreeItem]:
    """Build a nested tree from a flat list of nodes."""
    children_by_parent: dict[uuid.UUID | None, list[Node]] = defaultdict(list)
    for node in nodes:
        children_by_parent[node.parent_id].append(node)

    for siblings in children_by_parent.values():
        siblings.sort(key=lambda node: (node.sort_order, node.title))

    def build_branch(parent_id: uuid.UUID | None) -> list[NodeTreeItem]:
        return [
            NodeTreeItem(
                id=node.id,
                parent_id=node.parent_id,
                title=node.title,
                sort_order=node.sort_order,
                has_content=node.content_md is not None,
                children=build_branch(node.id),
            )
            for node in children_by_parent[parent_id]
        ]

    return build_branch(None)
