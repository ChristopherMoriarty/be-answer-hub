from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
