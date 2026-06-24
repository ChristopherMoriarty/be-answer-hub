from fastapi import FastAPI

from app.api.base import router as base_router
from app.api.cv import router as cv_router
from app.api.nodes import router as nodes_router


def init_routes(app_instance: "FastAPI") -> None:
    """Register all API routers in the FastAPI application."""
    app_instance.include_router(base_router)
    app_instance.include_router(nodes_router)
    app_instance.include_router(cv_router)
