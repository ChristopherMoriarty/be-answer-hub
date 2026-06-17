from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.node_repository import NodeRepository


async def get_node_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[NodeRepository, None]:
    """Provide a NodeRepository bound to the request session."""
    yield NodeRepository(session)
