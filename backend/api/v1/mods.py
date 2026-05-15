"""Mods API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from loguru import logger
from backend.services.modrinth_client import ModrinthClient

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ModrinthProject(BaseModel):
    """Мод с Modrinth."""
    project_id: str
    slug: str
    title: str
    description: str
    categories: List[str] = []
    downloads: int = 0
    icon_url: Optional[str] = None
    game_versions: List[str] = []
    loaders: List[str] = []


class ModrinthVersion(BaseModel):
    """Версия мода."""
    version_id: str
    project_id: str
    version_number: str
    game_versions: List[str]
    loaders: List[str]
    files: List[dict]


class ModSearchResponse(BaseModel):
    """Ответ поиска модов."""
    results: List[ModrinthProject]
    total: int
    offset: int
    limit: int


class ModInstallRequest(BaseModel):
    """Запрос на установку мода."""
    project_id: str
    version_id: Optional[str] = None
    game_version: Optional[str] = None
    loader: Optional[str] = None
    instance_name: Optional[str] = Field(None, description="Имя инстанса (если не указан - в глобальную папку mods)")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/mods/search", response_model=ModSearchResponse)
async def search_mods(
    query: str = Query(..., min_length=1, description="Поисковый запрос"),
    game_version: Optional[str] = Query(None, description="Версия Minecraft"),
    loader: Optional[str] = Query(None, description="Загрузчик: forge, fabric, quilt"),
    limit: int = Query(10, ge=1, le=100, description="Количество результатов"),
    offset: int = Query(0, ge=0, description="Смещение")
):
    """Поиск модов на Modrinth."""
    client = ModrinthClient()
    try:
        data = await client.search(query, game_version=game_version, loader=loader, limit=limit, offset=offset)
        hits = data.get("hits", [])
        results = [
            ModrinthProject(
                project_id=h["project_id"],
                slug=h["slug"],
                title=h["title"],
                description=h["description"],
                categories=h.get("categories", []),
                downloads=h.get("downloads", 0),
                icon_url=h.get("icon_url"),
                game_versions=h.get("versions", []),
                loaders=h.get("display_categories", []),
            )
            for h in hits
        ]
        return ModSearchResponse(
            results=results,
            total=data.get("total_hits", 0),
            offset=offset,
            limit=limit
        )
    except Exception as e:
        logger.error(f"search_mods error: {e}")
        raise HTTPException(status_code=503, detail=f"Modrinth API unavailable: {e}")
    finally:
        await client.close()


@router.get("/mods/featured", response_model=List[ModrinthProject])
async def get_featured_mods(
    project_type: Optional[str] = Query(None, description="Тип проекта"),
    limit: int = Query(12, ge=1, le=50)
):
    """Получить популярные/рекомендуемые моды."""
    client = ModrinthClient()
    try:
        query = project_type or ""
        data = await client.search(query, limit=limit)
        hits = data.get("hits", [])
        return [
            ModrinthProject(
                project_id=h["project_id"],
                slug=h["slug"],
                title=h["title"],
                description=h["description"],
                categories=h.get("categories", []),
                downloads=h.get("downloads", 0),
                icon_url=h.get("icon_url"),
                game_versions=h.get("versions", []),
                loaders=h.get("display_categories", []),
            )
            for h in hits
        ]
    except Exception as e:
        logger.error(f"get_featured_mods error: {e}")
        return []
    finally:
        await client.close()


@router.get("/mods/{project_id}", response_model=ModrinthProject)
async def get_mod(project_id: str):
    """Получить информацию о моде."""
    client = ModrinthClient()
    try:
        data = await client.get_project(project_id)
        return ModrinthProject(
            project_id=data["id"],
            slug=data["slug"],
            title=data["title"],
            description=data["description"],
            categories=data.get("categories", []),
            downloads=data.get("downloads", 0),
            icon_url=data.get("icon_url"),
            game_versions=data.get("game_versions", []),
            loaders=data.get("loaders", []),
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        await client.close()


@router.get("/mods/{project_id}/versions", response_model=List[ModrinthVersion])
async def get_mod_versions(
    project_id: str,
    game_version: Optional[str] = None,
    loader: Optional[str] = None
):
    """Получить версии мода."""
    client = ModrinthClient()
    try:
        versions = await client.get_project_versions(project_id, game_version, loader)
        return [
            ModrinthVersion(
                version_id=v["id"],
                project_id=v["project_id"],
                version_number=v["version_number"],
                game_versions=v.get("game_versions", []),
                loaders=v.get("loaders", []),
                files=[{"url": f["url"], "filename": f["filename"], "primary": f["primary"]} for f in v.get("files", [])],
            )
            for v in versions
        ]
    finally:
        await client.close()


@router.post("/mods/download")
async def download_mod(request: ModInstallRequest):
    """Скачать мод."""
    from shared.paths import get_cache_dir
    client = ModrinthClient()
    try:
        versions = await client.get_project_versions(
            request.project_id,
            request.game_version,
            request.loader,
        )
        if not versions:
            raise HTTPException(status_code=404, detail="No compatible version found")

        version = versions[0]
        primary_files = [f for f in version.get("files", []) if f.get("primary")]
        file_info = primary_files[0] if primary_files else version["files"][0]

        dest = get_cache_dir() / "mods" / file_info["filename"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        await client.download_file(file_info["url"], str(dest))

        return {"status": "downloaded", "path": str(dest), "filename": file_info["filename"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"download_mod error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")
    finally:
        await client.close()


@router.post("/mods/install")
async def install_mod(request: ModInstallRequest):
    """Установить мод в инстанс."""
    from shared.paths import get_cache_dir
    from backend.core.instance import Instance

    client = ModrinthClient()
    try:
        versions = await client.get_project_versions(
            request.project_id,
            request.game_version,
            request.loader,
        )
        if not versions:
            raise HTTPException(status_code=404, detail="No compatible version found")

        version = versions[0]
        primary_files = [f for f in version.get("files", []) if f.get("primary")]
        file_info = primary_files[0] if primary_files else version["files"][0]

        if request.instance_name:
            instance = Instance.load(request.instance_name)
            if instance is None:
                raise HTTPException(status_code=404, detail=f"Instance '{request.instance_name}' not found")
            dest = instance.mods_dir / file_info["filename"]
        else:
            dest = get_cache_dir() / "mods" / file_info["filename"]

        dest.parent.mkdir(parents=True, exist_ok=True)
        await client.download_file(file_info["url"], str(dest))

        return {"status": "installed", "path": str(dest), "filename": file_info["filename"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"install_mod error: {e}")
        raise HTTPException(status_code=500, detail=f"Install failed: {e}")
    finally:
        await client.close()


@router.get("/mods/installed")
async def get_installed_mods(
    instance_name: Optional[str] = Query(None, description="Имя инстанса")
):
    """Получить список установленных модов."""
    from backend.core.instance import Instance

    if instance_name:
        instance = Instance.load(instance_name)
        if instance is None:
            raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")
        mods_dir = instance.mods_dir
    else:
        from shared.paths import get_data_dir
        mods_dir = get_data_dir() / ".minecraft" / "mods"

    if not mods_dir.exists():
        return []

    mods = []
    for f in mods_dir.iterdir():
        if f.suffix in (".jar", ".zip", ".disabled"):
            mods.append({"filename": f.name, "path": str(f), "size": f.stat().st_size})
    return mods


@router.delete("/mods/uninstall")
async def uninstall_mod(
    project_id: str,
    instance_name: Optional[str] = Query(None, description="Имя инстанса")
):
    """Удалить мод по project_id (поиск по имени файла)."""
    from backend.core.instance import Instance

    if instance_name:
        instance = Instance.load(instance_name)
        if instance is None:
            raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")
        mods_dir = instance.mods_dir
    else:
        from shared.paths import get_data_dir
        mods_dir = get_data_dir() / ".minecraft" / "mods"

    if not mods_dir.exists():
        raise HTTPException(status_code=404, detail="Mods directory not found")

    # Удаляем файлы, содержащие project_id в имени (приближенная логика)
    removed = []
    for f in mods_dir.iterdir():
        if project_id.lower() in f.name.lower() and f.suffix in (".jar", ".zip", ".disabled"):
            f.unlink()
            removed.append(f.name)

    if not removed:
        raise HTTPException(status_code=404, detail=f"Mod '{project_id}' not found")

    return {"status": "uninstalled", "project_id": project_id, "removed": removed}
