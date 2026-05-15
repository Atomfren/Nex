"""Modpacks API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class ModpacksAPI:
    """Клиент для работы с Modpacks API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def search(
        self,
        query: str,
        game_version: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Поиск модпаков."""
        params = {"query": query, "limit": limit, "offset": offset}
        if game_version:
            params["game_version"] = game_version
        return await self.client.get("/modpacks/search", params=params)

    async def install(
        self,
        project_id: str,
        version_id: Optional[str] = None,
        new_name: str = "",
    ) -> dict[str, Any]:
        """Установить модпак."""
        return await self.client.post("/modpacks/install", json={
            "project_id": project_id,
            "version_id": version_id,
            "new_name": new_name,
        })
