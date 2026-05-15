"""Auth API клиент."""

from typing import Any, Optional
from frontend.services.api_client import APIClient


class AuthAPI:
    """Клиент для работы с Auth API."""

    def __init__(self, api_client: APIClient):
        self.client = api_client

    async def offline_login(self, username: str) -> dict[str, Any]:
        """Офлайн авторизация."""
        return await self.client.post("/auth/offline/login", json={"username": username})

    async def microsoft_login_start(self, client_id: str) -> dict[str, Any]:
        """Начать Microsoft OAuth."""
        return await self.client.post("/auth/microsoft/login/start", params={"client_id": client_id})

    async def microsoft_login_complete(
        self,
        client_id: str,
        auth_code: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        """Завершить Microsoft OAuth."""
        return await self.client.post("/auth/microsoft/login/complete", json={
            "client_id": client_id,
            "auth_code": auth_code,
            "code_verifier": code_verifier,
        })

    async def microsoft_refresh(
        self,
        client_id: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Обновить Microsoft токен."""
        return await self.client.post("/auth/microsoft/refresh", json={
            "client_id": client_id,
            "refresh_token": refresh_token,
        })

    async def get_profile(self) -> Optional[dict[str, Any]]:
        """Получить текущий профиль."""
        try:
            return await self.client.get("/auth/profile")
        except Exception:
            return None

    async def logout(self) -> dict[str, Any]:
        """Выйти из аккаунта."""
        return await self.client.post("/auth/logout")
