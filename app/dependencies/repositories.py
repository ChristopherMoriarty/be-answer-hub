from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.database.session import get_session
from app.models.user import User
from app.repositories.cv_repository import CvRepository
from app.repositories.hiring_repository import HiringRepository
from app.repositories.node_repository import NodeRepository


async def get_node_repository(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
) -> AsyncGenerator[NodeRepository, None]:
    """Provide a NodeRepository bound to the signed-in user."""
    yield NodeRepository(session, user.id)


async def get_cv_repository(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
) -> AsyncGenerator[CvRepository, None]:
    """Provide a CvRepository bound to the signed-in user."""
    yield CvRepository(session, user.id)


async def get_hiring_repository(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
) -> AsyncGenerator[HiringRepository, None]:
    """Provide a HiringRepository bound to the signed-in user."""
    yield HiringRepository(session, user.id)
