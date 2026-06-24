from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies.repositories import (
    get_cv_repository,
    get_hiring_repository,
    get_node_repository,
)
from app.dependencies.clients import get_minio_client
from app.clients.minio import MinioClient
from app.repositories.cv_repository import CvRepository
from app.repositories.hiring_repository import HiringRepository
from app.repositories.node_repository import NodeRepository
from app.services.cv_service import CvService
from app.services.hiring_service import HiringService
from app.services.node_service import NodeService


async def get_node_service(
    session: AsyncSession = Depends(get_session),
    repository: NodeRepository = Depends(get_node_repository),
) -> AsyncGenerator[NodeService, None]:
    """Provide a NodeService bound to the request session."""
    yield NodeService(session, repository)


async def get_cv_service(
    session: AsyncSession = Depends(get_session),
    repository: CvRepository = Depends(get_cv_repository),
    minio: MinioClient = Depends(get_minio_client),
) -> AsyncGenerator[CvService, None]:
    """Provide a CvService bound to the request session."""
    yield CvService(session, repository, minio)


async def get_hiring_service(
    session: AsyncSession = Depends(get_session),
    repository: HiringRepository = Depends(get_hiring_repository),
) -> AsyncGenerator[HiringService, None]:
    """Provide a HiringService bound to the request session."""
    yield HiringService(session, repository)
