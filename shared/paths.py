"""Управление путями (shared)."""

import os
from pathlib import Path
from typing import Optional


def get_app_name() -> str:
    """Возвращает название приложения."""
    return "nexoralauncher"


def get_config_dir() -> Path:
    """Возвращает путь к директории конфигурации."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", ""))
    else:  # Linux/macOS
        base = Path.home() / ".config"
    
    return base / get_app_name()


def get_data_dir() -> Path:
    """Возвращает путь к директории данных."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", ""))
    else:  # Linux/macOS
        base = Path.home() / ".local" / "share"
    
    return base / get_app_name()


def get_cache_dir() -> Path:
    """Возвращает путь к директории кэша."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", ""))
    else:  # Linux/macOS
        base = Path.home() / ".cache"
    
    return base / get_app_name()


def get_instances_dir() -> Path:
    """Возвращает путь к директории инстансов."""
    return get_data_dir() / "instances"


def get_logs_dir() -> Path:
    """Возвращает путь к директории логов."""
    return get_data_dir() / "logs"


def ensure_directories() -> None:
    """Создаёт все необходимые директории."""
    dirs = [
        get_config_dir(),
        get_data_dir(),
        get_cache_dir(),
        get_instances_dir(),
        get_logs_dir(),
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_resources_dir() -> Path:
    """Возвращает путь к директории ресурсов."""
    # Для разработки
    return Path(__file__).parent.parent.parent / "resources"
