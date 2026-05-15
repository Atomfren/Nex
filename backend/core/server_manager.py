"""Управление списком серверов."""

import json
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

from shared.paths import get_config_dir


@dataclass
class Server:
    """Модель сервера."""
    id: str
    name: str
    host: str
    port: int
    description: str = ""
    icon_url: str = ""


class ServerManager:
    """Менеджер серверов (хранит в JSON)."""

    _servers_file = get_config_dir() / "servers.json"

    @classmethod
    def _load(cls) -> List[Server]:
        if not cls._servers_file.exists():
            return []
        try:
            data = json.loads(cls._servers_file.read_text(encoding="utf-8"))
            return [Server(**item) for item in data]
        except Exception:
            return []

    @classmethod
    def _save(cls, servers: List[Server]) -> None:
        cls._servers_file.parent.mkdir(parents=True, exist_ok=True)
        cls._servers_file.write_text(
            json.dumps([asdict(s) for s in servers], indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    @classmethod
    def list_servers(cls) -> List[Server]:
        return cls._load()

    @classmethod
    def get_server(cls, server_id: str) -> Optional[Server]:
        for s in cls._load():
            if s.id == server_id:
                return s
        return None

    @classmethod
    def add_server(cls, name: str, host: str, port: int = 25565) -> Server:
        servers = cls._load()
        server = Server(
            id=str(uuid.uuid4()),
            name=name,
            host=host,
            port=port
        )
        servers.append(server)
        cls._save(servers)
        return server

    @classmethod
    def update_server(cls, server_id: str, **kwargs) -> Optional[Server]:
        servers = cls._load()
        for s in servers:
            if s.id == server_id:
                for key, value in kwargs.items():
                    if hasattr(s, key):
                        setattr(s, key, value)
                cls._save(servers)
                return s
        return None

    @classmethod
    def delete_server(cls, server_id: str) -> bool:
        servers = cls._load()
        new_servers = [s for s in servers if s.id != server_id]
        if len(new_servers) != len(servers):
            cls._save(new_servers)
            return True
        return False
