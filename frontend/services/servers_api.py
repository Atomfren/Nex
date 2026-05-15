"""Servers API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class ServersAPI:
    """Клиент для работы с Servers API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def list(self) -> list[dict[str, Any]]:
        """Получить список серверов."""
        return await self.client.get("/servers/")

    async def get(self, server_id: str) -> dict[str, Any]:
        """Получить сервер по ID."""
        return await self.client.get(f"/servers/{server_id}")

    async def create(
        self,
        name: str,
        host: str,
        port: int = 25565,
    ) -> dict[str, Any]:
        """Добавить сервер."""
        return await self.client.post("/servers/", json={
            "name": name,
            "host": host,
            "port": port,
        })

    async def update(
        self,
        server_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Обновить сервер."""
        return await self.client.patch(f"/servers/{server_id}", json=kwargs)

    async def delete(self, server_id: str) -> None:
        """Удалить сервер."""
        await self.client.delete(f"/servers/{server_id}")

    async def ping(self, server_id: str) -> dict[str, Any]:
        """Ping сервера."""
        return await self.client.get(f"/servers/{server_id}/ping")

    async def connect(self, server_id: str) -> dict[str, Any]:
        """Подключиться к серверу (запустить Minecraft)."""
        return await self.client.post(f"/servers/{server_id}/connect")
