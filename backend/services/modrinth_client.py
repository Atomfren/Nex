"""Клиент API Modrinth."""

import httpx
from typing import Optional, List, Dict, Any

from loguru import logger

MODRINTH_API = "https://api.modrinth.com/v2"


class ModrinthClient:
    """HTTP клиент для Modrinth API."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=MODRINTH_API,
            headers={"User-Agent": "NexoraLauncher/0.1.0"},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def search(
        self,
        query: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Поиск проектов на Modrinth."""
        facets = []
        if game_version:
            facets.append(f'["versions:{game_version}"]')
        if loader:
            facets.append(f'["categories:{loader}"]')

        params: Dict[str, Any] = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        if facets:
            params["facets"] = f"[{','.join(facets)}]"

        resp = await self.client.get("/search", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Получает информацию о проекте."""
        resp = await self.client.get(f"/project/{project_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_project_versions(
        self,
        project_id: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Получает версии проекта."""
        params: Dict[str, Any] = {}
        if game_version:
            params["game_versions"] = f'["{game_version}"]'
        if loader:
            params["loaders"] = f'["{loader}"]'

        resp = await self.client.get(f"/project/{project_id}/version", params=params)
        resp.raise_for_status()
        return resp.json()

    async def download_file(self, url: str, dest: str) -> str:
        """Скачивает файл по URL."""
        async with self.client.stream("GET", url, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)
        return dest
