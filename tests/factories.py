import uuid

import factory

from app.models.node import Node


class NodeFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for hierarchical topic nodes."""

    id = factory.LazyFunction(uuid.uuid4)
    parent_id = None
    title = factory.Sequence(lambda n: f"Node {n}")
    content_md = None
    sort_order = factory.Sequence(lambda n: n)

    class Meta:
        model = Node


FACTORIES = {NodeFactory}
