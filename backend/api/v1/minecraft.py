"""Minecraft API endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict
import subprocess

from loguru import logger

from backend.core.minecraft import MinecraftManager

router = APIRouter()

# Глобальное хранилище запущенных процессов
_processes: Dict[int, subprocess.Popen] = {}


# ============================================================================
# Models
# ============================================================================

class LaunchRequest(BaseModel):
    """Запрос на запуск Minecraft."""
    version_id: str = Field(..., min_length=1, description="ID версии Minecraft")
    username: str = Field(..., min_length=1, max_length=16, description="Имя пользователя")
    java_path: str = Field(default="", description="Путь к Java (опционально)")
    jvm_profile: str = Field(
        default="default",
        description="Профиль JVM",
        json_schema_extra={"enum": ["default", "performance", "low"]}
    )
    max_memory: int = Field(default=4096, ge=512, le=65536, description="Макс. память (MB)")
    min_memory: int = Field(default=512, ge=256, description="Мин. память (MB)")


class LaunchResponse(BaseModel):
    """Ответ на запуск Minecraft."""
    pid: int
    version: str
    username: str
    status: str = "starting"


class VersionInfo(BaseModel):
    """Информация о версии Minecraft."""
    id: str
    type: str  # release, snapshot, addon
    release_time: str


class InstallVersionRequest(BaseModel):
    """Запрос на установку версии."""
    version_id: str = Field(..., min_length=1)
    callback_url: Optional[str] = Field(None, description="URL для callback'ов прогресса")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/minecraft/launch", response_model=LaunchResponse)
async def launch_minecraft(request: LaunchRequest):
    """Запустить Minecraft."""
    from backend.core.auth import AuthManager
    import asyncio
    logger.info(f"Launch request: version={request.version_id}, user={request.username}")

    try:
        mc = MinecraftManager()
        auth = AuthManager()
        profile = auth.get_current_profile()

        username = request.username
        uuid = ""
        access_token = ""

        if profile:
            username = profile.username
            uuid = profile.uuid
            access_token = profile.access_token
            logger.debug(f"Using authenticated profile: {username}")

        java_path = request.java_path or mc.get_java_executable() or "java"
        logger.debug(f"Java path: {java_path}")

        # Проверяем и устанавливаем версию если не установлена (синхронно)
        if not mc.is_version_installed(request.version_id):
            logger.info(f"Version {request.version_id} not installed, installing...")
            # Запускаем установку в thread pool чтобы не блокировать event loop
            await asyncio.get_event_loop().run_in_executor(None, mc.install_version, request.version_id)
            logger.info(f"Version {request.version_id} installed")

        process = mc.launch(
            version_id=request.version_id,
            username=username,
            uuid=uuid,
            access_token=access_token,
            java_path=java_path,
            max_memory=request.max_memory,
            min_memory=request.min_memory,
        )

        _processes[process.pid] = process
        logger.info(f"Minecraft launched: pid={process.pid}, version={request.version_id}, user={username}")
        return LaunchResponse(
            pid=process.pid,
            version=request.version_id,
            username=username,
            status="running"
        )
    except Exception as e:
        logger.error(f"launch_minecraft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch Minecraft: {e}"
        )


@router.get("/minecraft/versions/available", response_model=list[VersionInfo])
async def get_available_versions():
    """Получить список доступных версий Minecraft."""
    try:
        mc = MinecraftManager()
        versions = mc.get_available_versions()
        return [VersionInfo(**v) for v in versions]
    except Exception as e:
        logger.error(f"get_available_versions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch versions: {e}"
        )


@router.get("/minecraft/versions/installed", response_model=list[VersionInfo])
async def get_installed_versions():
    """Получить список установленных версий Minecraft."""
    mc = MinecraftManager()
    versions = mc.get_installed_versions()
    return [VersionInfo(**v) for v in versions]


@router.post("/minecraft/versions/{version_id}/install")
async def install_version(
    version_id: str, 
    request: Optional[InstallVersionRequest] = None
):
    """Установить версию Minecraft."""
    logger.info(f"Installing version {version_id}...")
    try:
        mc = MinecraftManager()
        # Синхронная установка с ретраями
        import asyncio
        await asyncio.get_event_loop().run_in_executor(None, mc.install_version, version_id)
        logger.info(f"Version {version_id} installed successfully")
        return {"status": "installed", "version": version_id}
    except Exception as e:
        logger.error(f"Failed to install {version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install {version_id}: {e}"
        )


@router.post("/minecraft/versions/{version_id}/install_forge")
async def install_forge(version_id: str):
    """Установить Forge для версии."""
    logger.info(f"Installing Forge for {version_id}...")
    try:
        mc = MinecraftManager()
        import asyncio
        await asyncio.get_event_loop().run_in_executor(None, mc.install_forge, version_id)
        logger.info(f"Forge installed for {version_id}")
        return {"status": "installed_forge", "version": version_id}
    except Exception as e:
        logger.error(f"Failed to install Forge for {version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install Forge: {e}"
        )


@router.post("/minecraft/versions/{version_id}/install_fabric")
async def install_fabric(version_id: str):
    """Установить Fabric для версии."""
    logger.info(f"Installing Fabric for {version_id}...")
    try:
        mc = MinecraftManager()
        import asyncio
        await asyncio.get_event_loop().run_in_executor(None, mc.install_fabric, version_id)
        logger.info(f"Fabric installed for {version_id}")
        return {"status": "installed_fabric", "version": version_id}
    except Exception as e:
        logger.error(f"Failed to install Fabric for {version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install Fabric: {e}"
        )


@router.get("/minecraft/status/{process_id}")
async def get_process_status(process_id: int):
    """Получить статус процесса Minecraft."""
    process = _processes.get(process_id)
    if process is None:
        return {"status": "not_found", "pid": process_id}
    if process.poll() is None:
        return {"status": "running", "pid": process_id}
    else:
        return {"status": "stopped", "pid": process_id}


@router.delete("/minecraft/stop/{process_id}")
async def stop_minecraft(process_id: int):
    """Остановить процесс Minecraft."""
    process = _processes.get(process_id)
    if process is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process {process_id} not found"
        )
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    return {"status": "stopped", "pid": process_id}
