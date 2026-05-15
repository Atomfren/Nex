"""API v1 router aggregation."""

from fastapi import APIRouter

from backend.api.v1 import (
    health,
    instances,
    minecraft,
    mods,
    modpacks,
    auth,
    ai,
    settings,
    servers,
)

router = APIRouter()

# Подключение всех router'ов
router.include_router(health.router)
router.include_router(instances.router)
router.include_router(minecraft.router)
router.include_router(mods.router)
router.include_router(modpacks.router)
router.include_router(auth.router)
router.include_router(ai.router)
router.include_router(settings.router)
router.include_router(servers.router)
