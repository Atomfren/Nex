"""Shared modules - общие модули для backend и frontend."""

from shared.config import AppConfig
from shared.crypto import TokenVault
from shared.i18n import t, set_language, get_language
from shared.paths import (
    get_app_name,
    get_config_dir,
    get_data_dir,
    get_cache_dir,
    get_instances_dir,
    get_logs_dir,
    ensure_directories,
)

__all__ = [
    "AppConfig",
    "TokenVault",
    "t",
    "set_language",
    "get_language",
    "get_app_name",
    "get_config_dir",
    "get_data_dir",
    "get_cache_dir",
    "get_instances_dir",
    "get_logs_dir",
    "ensure_directories",
]
# - i18n.py
# - paths.py
# - perf.py

# Также перенести:
# - core/instance.py -> shared/models.py (DTO models)
