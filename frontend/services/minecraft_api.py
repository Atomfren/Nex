"""Minecraft API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class MinecraftAPI:
    """Клиент для работы с Minecraft API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def get_available_versions(self) -> list[dict[str, Any]]:
        """Получить список доступных версий Minecraft."""
        return await self.client.get("/minecraft/versions/available")

    async def get_installed_versions(self) -> list[dict[str, Any]]:
        """Получить список установленных версий."""
        return await self.client.get("/minecraft/versions/installed")

    async def install_version(self, version_id: str) -> dict[str, Any]:
        """Установить версию Minecraft."""
        return await self.client.post(f"/minecraft/versions/{version_id}/install", timeout=300)  # 5 минут

    async def install_forge(self, version_id: str) -> dict[str, Any]:
        """Установить Forge."""
        return await self.client.post(f"/minecraft/versions/{version_id}/install_forge")

    async def install_fabric(self, version_id: str) -> dict[str, Any]:
        """Установить Fabric."""
        return await self.client.post(f"/minecraft/versions/{version_id}/install_fabric")

    async def launch(
        self,
        version_id: str,
        username: str,
        java_path: str = "",
        max_memory: int = 4096,
        min_memory: int = 512,
    ) -> dict[str, Any]:
        """Запустить Minecraft."""
        return await self.client.post("/minecraft/launch", json={
            "version_id": version_id,
            "username": username,
            "java_path": java_path,
            "max_memory": max_memory,
            "min_memory": min_memory,
        }, timeout=120)  # 2 минуты на установку + запуск

    async def get_status(self, process_id: int) -> dict[str, Any]:
        """Получить статус процесса."""
        return await self.client.get(f"/minecraft/status/{process_id}")

    async def stop(self, process_id: int) -> dict[str, Any]:
        """Остановить Minecraft."""
        return await self.client.delete(f"/minecraft/stop/{process_id}")
