"""HTTP клиент для общения с backend API."""

import aiohttp
from typing import Any, Optional
from loguru import logger


_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30)


class APIClient:
    """HTTP клиент для общения с backend сервисом."""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url

    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        **kwargs
    ) -> dict[str, Any]:
        """Выполняет GET запрос."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url}")
        
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            async with session.get(url, params=params, **kwargs) as resp:
                data = await resp.json()
                logger.debug(f"GET {url} -> {resp.status}")
                return data

    async def post(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> dict[str, Any]:
        """Выполняет POST запрос."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"POST {url}")
        _timeout = aiohttp.ClientTimeout(total=timeout) if timeout else _DEFAULT_TIMEOUT
        
        async with aiohttp.ClientSession(timeout=_timeout) as session:
            async with session.post(url, json=json, data=data, **kwargs) as resp:
                if resp.status == 204:
                    logger.debug(f"POST {url} -> {resp.status}")
                    return {}
                result = await resp.json()
                logger.debug(f"POST {url} -> {resp.status}")
                return result

    async def patch(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        **kwargs
    ) -> dict[str, Any]:
        """Выполняет PATCH запрос."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"PATCH {url}")
        
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            async with session.patch(url, json=json, **kwargs) as resp:
                if resp.status == 204:
                    logger.debug(f"PATCH {url} -> {resp.status}")
                    return {}
                result = await resp.json()
                logger.debug(f"PATCH {url} -> {resp.status}")
                return result

    async def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> None:
        """Выполняет DELETE запрос."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"DELETE {url}")
        
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            async with session.delete(url, **kwargs) as resp:
                logger.debug(f"DELETE {url} -> {resp.status}")

    async def health_check(self) -> dict[str, Any]:
        """Проверяет работоспособность backend."""
        return await self.get("/health")

    async def close(self) -> None:
        """Ноп (сессии управляются через async with)."""
        pass
