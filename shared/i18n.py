"""Локализация (shared)."""

import json
from pathlib import Path
from typing import Any

# Встроенные переводы (fallback)
_BUILTIN: dict[str, dict[str, str]] = {
    "ru": {
        "app.title": "NexoraLauncher",
        "nav.home": "🏠  Главная",
        "nav.instances": "📁  Инстансы",
        "nav.versions": "📦  Версии",
        "nav.mods": "🧩  Моды",
        "nav.modpacks": "📦  Модпаки",
        "nav.maps": "🗺️  Карты",
        "nav.resourcepacks": "🎨  Ресурспаки",
        "nav.shaders": "🌈  Шейдеры",
        "nav.servers": "🖥️  Серверы",
        "nav.ai": "🤖  AI Помощник",
        "nav.settings": "⚙️  Настройки",
    },
    "en": {
        "app.title": "NexoraLauncher",
        "nav.home": "🏠  Home",
        "nav.instances": "📁  Instances",
        "nav.versions": "📦  Versions",
        "nav.mods": "🧩  Mods",
        "nav.modpacks": "📦  Modpacks",
        "nav.maps": "🗺️  Maps",
        "nav.resourcepacks": "🎨  Resource Packs",
        "nav.shaders": "🌈  Shaders",
        "nav.servers": "🖥️  Servers",
        "nav.ai": "🤖  AI Assistant",
        "nav.settings": "⚙️  Settings",
    },
}

_current_lang = "ru"


def set_language(lang: str) -> None:
    """Устанавливает текущий язык."""
    global _current_lang
    if lang in _BUILTIN:
        _current_lang = lang


def get_language() -> str:
    """Возвращает текущий язык."""
    return _current_lang


def t(key: str, **kwargs: Any) -> str:
    """Возвращает перевод по ключу с подстановкой переменных."""
    text = _BUILTIN.get(_current_lang, _BUILTIN["ru"]).get(key, key)
    try:
        return text.format(**kwargs)
    except KeyError:
        return text


def load_external_lang(path: Path) -> None:
    """Загружает внешний файл перевода и мержит с встроенным."""
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for lang, translations in data.items():
            if lang in _BUILTIN:
                _BUILTIN[lang].update(translations)
            else:
                _BUILTIN[lang] = dict(translations)
    except Exception:
        pass
