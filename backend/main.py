"""FastAPI приложение для NexoraLauncher Backend."""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для импорта модулей
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.v1 import (
    health,
    instances,
    minecraft,
    mods,
    modpacks,
    auth,
    ai,
    settings as settings_router,
    servers,
)
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    # Startup
    logger.info(f"{settings.app_name} v{settings.app_version} запускается...")
    logger.info(f"Host: {settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Backend завершает работу...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API для NexoraLauncher - Minecraft Launcher",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware (для будущих веб-клиентов)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "message": "NexoraLauncher Backend API",
        "version": settings.app_version,
        "docs": "/docs",
    }


# Подключение API router'ов
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(instances.router, prefix="/api/v1", tags=["instances"])
app.include_router(minecraft.router, prefix="/api/v1", tags=["minecraft"])
app.include_router(mods.router, prefix="/api/v1", tags=["mods"])
app.include_router(modpacks.router, prefix="/api/v1", tags=["modpacks"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(ai.router, prefix="/api/v1", tags=["ai"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["settings"])
app.include_router(servers.router, prefix="/api/v1", tags=["servers"])
