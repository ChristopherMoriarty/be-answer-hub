from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.cv_repository import CvRepository
from app.repositories.hiring_repository import HiringRepository
from app.repositories.node_repository import NodeRepository


async def get_node_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[NodeRepository, None]:
    """Provide a NodeRepository bound to the request session."""
    yield NodeRepository(session)


async def get_cv_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[CvRepository, None]:
    """Provide a CvRepository bound to the request session."""
    yield CvRepository(session)


async def get_hiring_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[HiringRepository, None]:
    """Provide a HiringRepository bound to the request session."""
    yield HiringRepository(session)
