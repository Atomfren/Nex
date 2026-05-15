"""Settings API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from loguru import logger
from shared.config import AppConfig
from backend.core.java_detector import find_java_installations

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class SettingsResponse(BaseModel):
    """Ответ с настройками."""
    appearance_mode: str = Field(..., description="Тема: dark/light")
    color_theme: str = Field(..., description="Цветовая тема")
    window_width: int = Field(..., description="Ширина окна")
    window_height: int = Field(..., description="Высота окна")
    fullscreen: bool = Field(..., description="Полноэкранный режим")
    java_path: str = Field(..., description="Путь к Java")
    max_memory: int = Field(..., description="Макс. память (MB)")
    min_memory: int = Field(..., description="Мин. память (MB)")
    jvm_profile: str = Field(..., description="Профиль JVM")
    language: str = Field(..., description="Язык")
    last_username: str = Field(..., description="Последнее имя пользователя")
    last_version: str = Field(..., description="Последняя версия")


class SettingsUpdate(BaseModel):
    """Настройки для обновления (все опционально)."""
    appearance_mode: Optional[str] = None
    color_theme: Optional[str] = None
    window_width: Optional[int] = None
    window_height: Optional[int] = None
    fullscreen: Optional[bool] = None
    java_path: Optional[str] = None
    max_memory: Optional[int] = Field(None, ge=512, le=65536)
    min_memory: Optional[int] = Field(None, ge=256)
    jvm_profile: Optional[str] = None
    language: Optional[str] = None
    last_username: Optional[str] = None
    last_version: Optional[str] = None


class JavaInfo(BaseModel):
    """Информация о найденной Java."""
    path: str
    version: str
    vendor: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/settings/", response_model=SettingsResponse)
async def get_settings():
    """Получить текущие настройки."""
    try:
        config = AppConfig.load()
        return SettingsResponse(
            appearance_mode=config.appearance_mode,
            color_theme=config.color_theme,
            window_width=config.window_width,
            window_height=config.window_height,
            fullscreen=config.fullscreen,
            java_path=config.java_path,
            max_memory=config.max_memory,
            min_memory=config.min_memory,
            jvm_profile=config.jvm_profile,
            language=config.language,
            last_username=config.last_username,
            last_version=config.last_version,
        )
    except Exception as e:
        logger.error(f"get_settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load settings: {e}"
        )


@router.patch("/settings/", response_model=SettingsResponse)
async def update_settings(settings: SettingsUpdate):
    """Обновить настройки."""
    try:
        config = AppConfig.load()
        for key, value in settings.model_dump(exclude_unset=True).items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        config.save()
        return await get_settings()
    except Exception as e:
        logger.error(f"update_settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {e}"
        )


@router.get("/settings/java/", response_model=list[JavaInfo])
async def get_java_info():
    """Получить информацию о Java."""
    try:
        java_list = find_java_installations()
        return [JavaInfo(path=j.path, version=j.version, vendor=j.vendor) for j in java_list]
    except Exception as e:
        logger.error(f"get_java_info error: {e}")
        return []


@router.post("/settings/java/detect", response_model=list[JavaInfo])
async def detect_java():
    """Автодетект Java на системе."""
    try:
        java_list = find_java_installations()
        return [JavaInfo(path=j.path, version=j.version, vendor=j.vendor) for j in java_list]
    except Exception as e:
        logger.error(f"detect_java error: {e}")
        return []
