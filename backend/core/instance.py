"""Управление инстансами (заготовка для миграции)."""

import json
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from loguru import logger


class Instance:
    """Инстанс Minecraft."""
    
    def __init__(
        self,
        name: str,
        version: str,
        mod_loader: str = "vanilla",
        loader_version: str = "",
        java_path: str = "",
        max_memory: int = 4096,
        min_memory: int = 512,
        width: int = 1280,
        height: int = 720,
        fullscreen: bool = False,
        created_at: str = "",
        last_played: str = "",
        play_count: int = 0
    ):
        self.name = name
        self.version = version
        self.mod_loader = mod_loader
        self.loader_version = loader_version
        self.java_path = java_path
        self.max_memory = max_memory
        self.min_memory = min_memory
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.created_at = created_at or datetime.now().isoformat()
        self.last_played = last_played
        self.play_count = play_count
        logger.debug(f"Instance '{name}' initialized (v{version}, {mod_loader})")
    
    @property
    def path(self) -> Path:
        """Путь к директории инстанса."""
        from shared.paths import get_instances_dir
        return get_instances_dir() / self.name
    
    @property
    def game_dir(self) -> Path:
        """Путь к .minecraft внутри инстанса."""
        return self.path / ".minecraft"
    
    @property
    def mods_dir(self) -> Path:
        """Путь к папке модов."""
        return self.game_dir / "mods"
    
    def ensure_dirs(self) -> None:
        """Создаёт необходимые директории."""
        self.game_dir.mkdir(parents=True, exist_ok=True)
        self.mods_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Сериализует в dict."""
        return {
            "name": self.name,
            "version": self.version,
            "mod_loader": self.mod_loader,
            "loader_version": self.loader_version,
            "java_path": self.java_path,
            "max_memory": self.max_memory,
            "min_memory": self.min_memory,
            "width": self.width,
            "height": self.height,
            "fullscreen": self.fullscreen,
            "created_at": self.created_at,
            "last_played": self.last_played,
            "play_count": self.play_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Instance":
        """Десериализует из dict."""
        allowed = cls.__init__.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)
    
    def save(self) -> None:
        """Сохраняет инстанс в JSON."""
        self.ensure_dirs()
        config_path = self.path / "instance.json"
        config_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info(f"Instance '{self.name}' saved to {config_path}")
    
    @classmethod
    def load(cls, name: str) -> Optional["Instance"]:
        """Загружает инстанс по имени."""
        from shared.paths import get_instances_dir
        config_path = get_instances_dir() / name / "instance.json"
        if not config_path.exists():
            logger.debug(f"Instance '{name}' not found at {config_path}")
            return None
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            logger.debug(f"Instance '{name}' loaded from {config_path}")
            return cls.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load instance '{name}': {e}")
            return None
    
    def on_launch(self) -> None:
        """Обновляет статистику при запуске."""
        self.last_played = datetime.now().isoformat()
        self.play_count += 1
        self.save()
        logger.info(f"Instance '{self.name}' launched (count: {self.play_count})")


class InstanceManager:
    """Менеджер всех инстансов."""
    
    @staticmethod
    def list_instances() -> list[Instance]:
        """Возвращает список всех инстансов."""
        from shared.paths import get_instances_dir
        instances_dir = get_instances_dir()
        if not instances_dir.exists():
            logger.debug(f"Instances dir does not exist: {instances_dir}")
            return []
        
        instances = []
        for path in instances_dir.iterdir():
            if path.is_dir():
                instance = Instance.load(path.name)
                if instance:
                    instances.append(instance)
        logger.info(f"Listed {len(instances)} instance(s) from {instances_dir}")
        return instances
    
    @staticmethod
    def create(name: str, version: str, mod_loader: str = "vanilla") -> Instance:
        """Создаёт новый инстанс."""
        from shared.paths import get_instances_dir
        target = get_instances_dir() / name / "instance.json"
        if target.exists():
            logger.warning(f"Instance '{name}' already exists at {target}")
            raise FileExistsError(f"Instance '{name}' already exists")
        
        instance = Instance(name=name, version=version, mod_loader=mod_loader)
        instance.save()
        logger.info(f"Instance '{name}' created (v{version}, {mod_loader})")
        return instance
    
    @staticmethod
    def delete(name: str) -> bool:
        """Удаляет инстанс."""
        from shared.paths import get_instances_dir
        path = get_instances_dir() / name
        if not path.exists():
            logger.warning(f"Cannot delete instance '{name}': not found at {path}")
            return False
        shutil.rmtree(path)
        logger.info(f"Instance '{name}' deleted from {path}")
        return True
