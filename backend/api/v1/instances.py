"""Instances API endpoints."""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from loguru import logger
from backend.core.instance import Instance, InstanceManager

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class InstanceBase(BaseModel):
    """Базовая модель инстанса."""
    name: str = Field(..., min_length=1, max_length=100, description="Название инстанса")
    version: str = Field(..., min_length=1, description="Версия Minecraft")
    mod_loader: str = Field(
        default="vanilla", 
        description="Загрузчик модов",
        json_schema_extra={"enum": ["vanilla", "forge", "fabric", "quilt"]}
    )
    loader_version: str = Field(default="", description="Версия загрузчика")


class InstanceCreate(InstanceBase):
    """Модель для создания инстанса."""
    pass


class InstanceUpdate(BaseModel):
    """Модель для обновления инстанса."""
    version: Optional[str] = Field(None, min_length=1)
    mod_loader: Optional[str] = Field(None, json_schema_extra={"enum": ["vanilla", "forge", "fabric", "quilt"]})
    loader_version: Optional[str] = None
    java_path: Optional[str] = None
    max_memory: Optional[int] = Field(None, ge=512, le=65536)
    min_memory: Optional[int] = Field(None, ge=256)
    width: Optional[int] = Field(None, ge=800, le=3840)
    height: Optional[int] = Field(None, ge=600, le=2160)
    fullscreen: Optional[bool] = None


class InstanceResponse(InstanceBase):
    """Модель ответа инстанса."""
    java_path: str = ""
    max_memory: int = 4096
    min_memory: int = 512
    width: int = 1280
    height: int = 720
    fullscreen: bool = False
    created_at: str
    last_played: Optional[str] = None
    play_count: int = 0


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/instances/", response_model=list[InstanceResponse])
async def list_instances():
    """Получить список всех инстансов."""
    logger.info("Listing all instances")
    try:
        instances = InstanceManager.list_instances()
        result = [InstanceResponse(**i.to_dict()) for i in instances]
        logger.info(f"Listed {len(result)} instance(s)")
        return result
    except Exception as e:
        logger.error(f"list_instances error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list instances: {e}"
        )


@router.get("/instances/{name}", response_model=InstanceResponse)
async def get_instance(name: str):
    """Получить инстанс по имени."""
    logger.info(f"Getting instance '{name}'")
    instance = Instance.load(name)
    if instance is None:
        logger.warning(f"Instance '{name}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance '{name}' not found"
        )
    logger.info(f"Instance '{name}' loaded successfully")
    return InstanceResponse(**instance.to_dict())


@router.post("/instances/", response_model=InstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_instance(data: InstanceCreate):
    """Создать новый инстанс."""
    logger.info(f"Creating instance: name={data.name}, version={data.version}, loader={data.mod_loader}")
    try:
        instance = InstanceManager.create(
            name=data.name,
            version=data.version,
            mod_loader=data.mod_loader,
        )
        instance.loader_version = data.loader_version
        instance.save()
        logger.info(f"Instance '{data.name}' created successfully")
        return InstanceResponse(**instance.to_dict())
    except FileExistsError as e:
        logger.warning(f"Instance '{data.name}' already exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"create_instance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create instance: {e}"
        )


@router.patch("/instances/{name}", response_model=InstanceResponse)
async def update_instance(name: str, data: InstanceUpdate):
    """Обновить инстанс."""
    logger.info(f"Updating instance '{name}'")
    instance = Instance.load(name)
    if instance is None:
        logger.warning(f"Instance '{name}' not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance '{name}' not found"
        )
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None and hasattr(instance, key):
            setattr(instance, key, value)
    instance.save()
    logger.info(f"Instance '{name}' updated: {updates}")
    return InstanceResponse(**instance.to_dict())


@router.delete("/instances/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instance(name: str):
    """Удалить инстанс."""
    logger.info(f"Deleting instance '{name}'")
    if not InstanceManager.delete(name):
        logger.warning(f"Instance '{name}' not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance '{name}' not found"
        )
    logger.info(f"Instance '{name}' deleted successfully")


@router.post("/instances/{name}/export")
async def export_instance(name: str):
    """Экспорт инстанса в .zip архив."""
    logger.info(f"Exporting instance '{name}'")
    from backend.core.pack_manager import PackManager
    try:
        path = PackManager.export_instance(name)
        logger.info(f"Instance '{name}' exported to {path}")
        return {"status": "exported", "path": str(path)}
    except FileNotFoundError:
        logger.warning(f"Instance '{name}' not found for export")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance '{name}' not found"
        )


class ImportInstanceRequest(BaseModel):
    """Запрос на импорт инстанса."""
    file_path: str = Field(..., description="Путь к .zip или .mrpack файлу")
    new_name: str = Field(..., description="Новое название инстанса")


@router.post("/instances/import")
async def import_instance(request: ImportInstanceRequest):
    """Импорт инстанса из архива."""
    logger.info(f"Importing instance from {request.file_path} as '{request.new_name}'")
    from backend.core.pack_manager import PackManager
    from pathlib import Path

    path = Path(request.file_path)
    if not path.exists():
        logger.warning(f"Import file not found: {request.file_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File not found: {request.file_path}"
        )

    if request.file_path.endswith(".mrpack"):
        instance = PackManager.import_mrpack(path, request.new_name)
    else:
        instance = PackManager.import_zip(path, request.new_name)

    logger.info(f"Instance '{request.new_name}' imported successfully")
    return {"status": "imported", "name": request.new_name, "instance": instance.to_dict()}
