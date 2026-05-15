"""Точка входа для frontend GUI на PyQt6."""

import sys
import subprocess
import time
import requests
from pathlib import Path

# Включаем UTF-8 для вывода в консоль на Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Добавляем ARCHITECTURE в sys.path для корректных импортов
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from frontend.utils.logger import logger


def start_backend_server() -> subprocess.Popen | None:
    """Запускает backend сервер как subprocess (если не запущен)."""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=2)
        if response.status_code == 200:
            logger.info("Backend already running")
            return None
    except requests.ConnectionError:
        logger.info("Backend not detected, starting...")
    
    logger.info("Starting backend server...")
    project_root = Path(__file__).parent.parent
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    
    for i in range(30):
        try:
            response = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=1)
            if response.status_code == 200:
                logger.info("Backend started successfully")
                return process
        except requests.ConnectionError:
            time.sleep(0.5)
    
    logger.error("Backend failed to start within timeout")
    return process


def main():
    """Главная функция."""
    from PyQt6.QtWidgets import QApplication
    from frontend.app import NexoraLauncherApp

    logger.info("NexoraLauncher frontend starting...")

    # Запускаем backend если нужно
    backend_process = start_backend_server()
    
    try:
        # Создаём приложение PyQt6
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        logger.info("PyQt6 application created")

        # Запускаем GUI
        window = NexoraLauncherApp()
        window.show()
        logger.info("Main window shown")

        # Запускаем главный цикл
        sys.exit(app.exec())
    except Exception as e:
        logger.exception(f"Frontend crashed: {e}")
        raise
    finally:
        # Останавливаем backend если запускали сами
        if backend_process:
            logger.info("Stopping backend...")
            backend_process.terminate()
            backend_process.wait()


if __name__ == "__main__":
    main()
