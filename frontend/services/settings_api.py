"""Settings API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class SettingsAPI:
    """Клиент для работы с Settings API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def get(self) -> dict[str, Any]:
        """Получить текущие настройки."""
        return await self.client.get("/settings/")

    async def update(self, **kwargs) -> dict[str, Any]:
        """Обновить настройки."""
        return await self.client.patch("/settings/", json=kwargs)

    async def get_java_info(self) -> list[dict[str, Any]]:
        """Получить информацию о Java."""
        return await self.client.get("/settings/java/")

    async def detect_java(self) -> list[dict[str, Any]]:
        """Автодетект Java на системе."""
        return await self.client.post("/settings/java/detect")
