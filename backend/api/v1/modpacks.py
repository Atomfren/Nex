"""Modpacks API endpoints."""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List

from loguru import logger
from backend.services.modrinth_client import ModrinthClient
from backend.core.pack_manager import PackManager

router = APIRouter()


class ModpackBase(BaseModel):
    project_id: str
    slug: str
    title: str
    description: str
    icon_url: Optional[str] = None
    downloads: int = 0
    game_versions: List[str] = []


class ModpackSearchResponse(BaseModel):
    results: List[ModpackBase]
    total: int
    offset: int
    limit: int


class ModpackInstallRequest(BaseModel):
    project_id: str
    version_id: Optional[str] = None
    new_name: str = Field(..., min_length=1)


@router.get("/modpacks/search", response_model=ModpackSearchResponse)
async def search_modpacks(
    query: str = Query(..., min_length=1),
    game_version: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Поиск модпаков на Modrinth."""
    client = ModrinthClient()
    try:
        facets = ['["project_type:modpack"]']
        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
            "facets": f"[{','.join(facets)}]",
        }
        if game_version:
            params["facets"] = f'[["project_type:modpack"],["versions:{game_version}"]]'

        data = await client.client.get("/search", params=params)
        data.raise_for_status()
        json_data = data.json()
        hits = json_data.get("hits", [])
        return ModpackSearchResponse(
            results=[
                ModpackBase(
                    project_id=h["project_id"],
                    slug=h["slug"],
                    title=h["title"],
                    description=h["description"],
                    icon_url=h.get("icon_url"),
                    downloads=h.get("downloads", 0),
                    game_versions=h.get("versions", []),
                )
                for h in hits
            ],
            total=json_data.get("total_hits", 0),
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"search_modpacks error: {e}")
        raise HTTPException(status_code=503, detail=f"Modrinth API unavailable: {e}")
    finally:
        await client.close()


@router.post("/modpacks/install")
async def install_modpack(
    request: ModpackInstallRequest,
    background_tasks: BackgroundTasks,
):
    """Установить модпак."""
    client = ModrinthClient()
    try:
        versions = await client.get_project_versions(request.project_id)
        if not versions:
            raise HTTPException(status_code=404, detail="No versions found")

        version = versions[0]
        if request.version_id:
            for v in versions:
                if v["id"] == request.version_id:
                    version = v
                    break

        primary_files = [f for f in version.get("files", []) if f.get("primary")]
        file_info = primary_files[0] if primary_files else version["files"][0]

        from shared.paths import get_cache_dir
        dest = get_cache_dir() / "modpacks" / file_info["filename"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        await client.download_file(file_info["url"], str(dest))

        # Импорт как инстанс
        instance = PackManager.import_mrpack(dest, request.new_name)
        return {
            "status": "installed",
            "instance": instance.to_dict(),
        }
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"install_modpack error: {e}")
        raise HTTPException(status_code=500, detail=f"Install failed: {e}")
    finally:
        await client.close()
