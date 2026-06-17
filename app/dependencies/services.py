from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies.repositories import get_node_repository
from app.repositories.node_repository import NodeRepository
from app.services.node_service import NodeService


async def get_node_service(
    session: AsyncSession = Depends(get_session),
    repository: NodeRepository = Depends(get_node_repository),
) -> AsyncGenerator[NodeService, None]:
    """Provide a NodeService bound to the request session."""
    yield NodeService(session, repository)
