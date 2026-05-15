"""Ping серверов Minecraft."""

from dataclasses import dataclass
from typing import Optional

from mcstatus import JavaServer
from loguru import logger


@dataclass
class PingResult:
    """Результат ping сервера."""
    online: bool
    player_count: Optional[int] = None
    max_players: Optional[int] = None
    version: Optional[str] = None
    motd: Optional[str] = None
    latency_ms: Optional[int] = None


async def ping_server(host: str, port: int = 25565, timeout: int = 5) -> PingResult:
    """Асинхронно пингует Minecraft сервер."""
    try:
        server = JavaServer.lookup(f"{host}:{port}", timeout=timeout)
        status = await server.async_status()
        return PingResult(
            online=True,
            player_count=status.players.online if status.players else 0,
            max_players=status.players.max if status.players else 0,
            version=status.version.name if status.version else None,
            motd=status.description if isinstance(status.description, str) else str(status.description),
            latency_ms=int(status.latency)
        )
    except Exception as e:
        logger.debug(f"Server ping failed for {host}:{port}: {e}")
        return PingResult(online=False)
