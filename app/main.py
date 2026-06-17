from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.exceptions_handler import register_exception_handlers
from app.core.logging import init_logger
from app.core.settings import settings
from app.database.session import db
from app.routes import init_routes


init_logger(settings.logger.level.value)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    logger.info("Starting API server")
    yield
    logger.info("Shutting down API server")
    await db.close()


app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    default_response_class=JSONResponse,
    lifespan=lifespan,
)

register_exception_handlers(app)
init_routes(app)
