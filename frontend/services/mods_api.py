"""Mods API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class ModsAPI:
    """Клиент для работы с Mods API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def search(
        self,
        query: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Поиск модов."""
        params = {"query": query, "limit": limit, "offset": offset}
        if game_version:
            params["game_version"] = game_version
        if loader:
            params["loader"] = loader
        return await self.client.get("/mods/search", params=params)

    async def get(self, project_id: str) -> dict[str, Any]:
        """Получить информацию о моде."""
        return await self.client.get(f"/mods/{project_id}")

    async def get_versions(
        self,
        project_id: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Получить версии мода."""
        params = {}
        if game_version:
            params["game_version"] = game_version
        if loader:
            params["loader"] = loader
        return await self.client.get(f"/mods/{project_id}/versions", params=params)

    async def download(
        self,
        project_id: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
        instance_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Скачать мод."""
        return await self.client.post("/mods/download", json={
            "project_id": project_id,
            "game_version": game_version,
            "loader": loader,
            "instance_name": instance_name,
        })

    async def install(
        self,
        project_id: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
        instance_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Установить мод в инстанс."""
        return await self.client.post("/mods/install", json={
            "project_id": project_id,
            "game_version": game_version,
            "loader": loader,
            "instance_name": instance_name,
        })

    async def get_installed(
        self,
        instance_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Получить список установленных модов."""
        params = {}
        if instance_name:
            params["instance_name"] = instance_name
        return await self.client.get("/mods/installed", params=params)

    async def uninstall(
        self,
        project_id: str,
        instance_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Удалить мод."""
        params = {"project_id": project_id}
        if instance_name:
            params["instance_name"] = instance_name
        return await self.client.delete("/mods/uninstall", params=params)

    async def get_featured(
        self,
        project_type: Optional[str] = None,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Получить популярные моды."""
        params = {"limit": limit}
        if project_type:
            params["project_type"] = project_type
        return await self.client.get("/mods/featured", params=params)
