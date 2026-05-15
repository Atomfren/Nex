"""Servers API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from loguru import logger
from backend.core.server_manager import ServerManager
from backend.core.server_ping import ping_server

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ServerBase(BaseModel):
    """Базовая модель сервера."""
    name: str = Field(..., min_length=1, max_length=100, description="Название сервера")
    host: str = Field(..., min_length=1, description="IP адрес или домен")
    port: int = Field(default=25565, ge=1, le=65535, description="Порт")


class ServerCreate(ServerBase):
    """Модель для создания сервера."""
    pass


class ServerResponse(ServerBase):
    """Модель ответа сервера."""
    id: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    last_online: Optional[datetime] = None
    player_count: Optional[int] = None
    max_players: Optional[int] = None
    version: Optional[str] = None
    motd: Optional[str] = None


class ServerPingResponse(BaseModel):
    """Ответ ping сервера."""
    online: bool
    player_count: Optional[int] = None
    max_players: Optional[int] = None
    version: Optional[str] = None
    motd: Optional[str] = None
    latency_ms: Optional[int] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/servers/", response_model=list[ServerResponse])
async def list_servers():
    """Получить список серверов."""
    try:
        servers = ServerManager.list_servers()
        return [
            ServerResponse(
                id=s.id,
                name=s.name,
                host=s.host,
                port=s.port,
                description=s.description,
                icon_url=s.icon_url,
            )
            for s in servers
        ]
    except Exception as e:
        logger.error(f"list_servers error: {e}")
        return []


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(server_id: str):
    """Получить информацию о сервере."""
    server = ServerManager.get_server(server_id)
    if server is None:
        raise HTTPException(
            status_code=404,
            detail=f"Server '{server_id}' not found"
        )
    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        description=server.description,
        icon_url=server.icon_url,
    )


@router.post("/servers/", response_model=ServerResponse, status_code=201)
async def create_server(server: ServerCreate):
    """Добавить сервер."""
    try:
        s = ServerManager.add_server(server.name, server.host, server.port)
        return ServerResponse(
            id=s.id,
            name=s.name,
            host=s.host,
            port=s.port,
        )
    except Exception as e:
        logger.error(f"create_server error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add server: {e}")


@router.patch("/servers/{server_id}")
async def update_server(server_id: str, server: ServerCreate):
    """Обновить сервер."""
    updated = ServerManager.update_server(
        server_id,
        name=server.name,
        host=server.host,
        port=server.port,
    )
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Server '{server_id}' not found"
        )
    return ServerResponse(
        id=updated.id,
        name=updated.name,
        host=updated.host,
        port=updated.port,
    )


@router.delete("/servers/{server_id}", status_code=204)
async def delete_server(server_id: str):
    """Удалить сервер."""
    if not ServerManager.delete_server(server_id):
        raise HTTPException(
            status_code=404,
            detail=f"Server '{server_id}' not found"
        )


@router.get("/servers/{server_id}/ping", response_model=ServerPingResponse)
async def ping_server_endpoint(server_id: str):
    """Ping сервера Minecraft."""
    try:
        server = ServerManager.get_server(server_id)
        if server is None:
            raise HTTPException(
                status_code=404,
                detail=f"Server '{server_id}' not found"
            )
        result = await ping_server(server.host, server.port)
        return ServerPingResponse(
            online=result.online,
            player_count=result.player_count,
            max_players=result.max_players,
            version=result.version,
            motd=result.motd,
            latency_ms=result.latency_ms,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ping_server error: {e}")
        return ServerPingResponse(online=False)


@router.post("/servers/{server_id}/connect")
async def connect_to_server(server_id: str):
    """Подключиться к серверу (запустить Minecraft с авто-подключением)."""
    from backend.core.minecraft import MinecraftManager
    from backend.core.auth import AuthManager

    try:
        server = ServerManager.get_server(server_id)
        if server is None:
            raise HTTPException(
                status_code=404,
                detail=f"Server '{server_id}' not found"
            )

        mc = MinecraftManager()
        profile = AuthManager.get_current_profile()
        username = profile.username if profile else "Player"
        uuid = profile.uuid if profile else ""
        access_token = profile.access_token if profile else ""

        process = mc.launch(
            version_id="latest",
            username=username,
            uuid=uuid,
            access_token=access_token,
            server=server.host,
            port=server.port,
        )

        return {
            "status": "launched",
            "pid": process.pid,
            "server": server.host,
            "port": server.port,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"connect_to_server error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch: {e}")
