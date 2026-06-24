import uuid

import factory

from app.models.cv import Cv
from app.models.hiring import HiringBoard, HiringBoardColumn, HiringProcess
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


class CvFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for stored CV PDF metadata."""

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.Sequence(lambda n: f"CV {n}")
    original_filename = "resume.pdf"
    storage_key = factory.LazyAttribute(lambda obj: f"cv/{obj.id}.pdf")
    file_size = 1024
    mime_type = "application/pdf"
    is_current = False
    notes = None

    class Meta:
        model = Cv


class HiringBoardFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for hiring boards."""

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.Sequence(lambda n: f"Board {n}")
    sort_order = factory.Sequence(lambda n: n)

    class Meta:
        model = HiringBoard


class HiringBoardColumnFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for hiring board step columns."""

    id = factory.LazyFunction(uuid.uuid4)
    board = factory.SubFactory(HiringBoardFactory)
    board_id = factory.SelfAttribute("board.id")
    step_kind = "applied"
    custom_title = None
    sort_order = factory.Sequence(lambda n: n)

    class Meta:
        model = HiringBoardColumn


class HiringProcessFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for hiring process rows."""

    id = factory.LazyFunction(uuid.uuid4)
    board = factory.SubFactory(HiringBoardFactory)
    board_id = factory.SelfAttribute("board.id")
    company = factory.Sequence(lambda n: f"Company {n}")
    source = ""
    result = "in_progress"
    offer_details = None
    notes = None
    sort_order = factory.Sequence(lambda n: n)

    class Meta:
        model = HiringProcess


FACTORIES = {
    NodeFactory,
    CvFactory,
    HiringBoardFactory,
    HiringBoardColumnFactory,
    HiringProcessFactory,
}
