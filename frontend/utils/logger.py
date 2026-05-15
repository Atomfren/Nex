"""Логирование для frontend."""

import sys
from pathlib import Path
from loguru import logger

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOG_FILE = _LOG_DIR / "frontend.log"

# Удаляем дефолтный handler
logger.remove()

# Console — только INFO и выше, без debug
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    colorize=True,
)

# File — всё включая DEBUG
logger.add(
    str(_LOG_FILE),
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} — {message}",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
)
