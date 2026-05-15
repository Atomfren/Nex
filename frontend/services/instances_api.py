"""Instances API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class InstancesAPI:
    """Клиент для работы с Instances API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def list(self) -> list[dict[str, Any]]:
        """Получить список всех инстансов."""
        return await self.client.get("/instances/")

    async def get(self, name: str) -> dict[str, Any]:
        """Получить инстанс по имени."""
        return await self.client.get(f"/instances/{name}")

    async def create(
        self,
        name: str,
        version: str,
        mod_loader: str = "vanilla",
        loader_version: str = ""
    ) -> dict[str, Any]:
        """Создать новый инстанс."""
        return await self.client.post(
            "/instances/",
            json={
                "name": name,
                "version": version,
                "mod_loader": mod_loader,
                "loader_version": loader_version
            }
        )

    async def update(self, name: str, **kwargs) -> dict[str, Any]:
        """Обновить инстанс."""
        return await self.client.patch(f"/instances/{name}", json=kwargs)

    async def delete(self, name: str) -> None:
        """Удалить инстанс."""
        await self.client.delete(f"/instances/{name}")

    async def export(self, name: str) -> dict[str, Any]:
        """Экспортировать инстанс."""
        return await self.client.post(f"/instances/{name}/export")

    async def import_instance(self, file_path: str, new_name: str) -> dict[str, Any]:
        """Импортировать инстанс из архива."""
        return await self.client.post(
            "/instances/import",
            json={"file_path": file_path, "new_name": new_name}
        )
