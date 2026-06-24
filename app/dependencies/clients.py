from fastapi import Request

from app.clients.minio import MinioClient


def get_minio_client(request: Request) -> MinioClient:
    """Provide the shared MinIO client from application state."""
    return request.app.state.minio_client
