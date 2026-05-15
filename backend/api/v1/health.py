"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from backend.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Ответ health check."""
    status: str
    version: str
    timestamp: str
    app_name: str


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Проверка работоспособности backend."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
        app_name=settings.app_name
    )


@router.get("/ping", tags=["health"])
async def ping():
    """Простой ping endpoint."""
    return {"pong": True, "timestamp": datetime.utcnow().isoformat()}
