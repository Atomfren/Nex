import os
import subprocess
import shutil
import glob
from pathlib import Path
from typing import Optional, List, Dict, Any
import json 
import minecraft_launcher_lib as mll
from loguru import logger

from shared.paths import get_data_dir


class MinecraftManager:
    """Менеджер Minecraft с улучшенной обработкой ошибок и логированием."""

    def __init__(self):
        # Гарантируем корректное представление пути
        self.minecraft_dir = Path(os.path.expanduser(str(get_data_dir()))) / ".minecraft"
        self.minecraft_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Minecraft directory set to: {self.minecraft_dir}")

    def get_available_versions(self) -> List[Dict[str, str]]:
        """Возвращает список доступных версий из Mojang."""
        try:
            version_list = mll.utils.get_version_list()
            return [
                {
                    "id": v["id"],
                    "type": v.get("type", "unknown"),
                    "release_time": str(v.get("releaseTime", "")) if v.get("releaseTime") else ""
                }
                for v in version_list
            ]
        except Exception as e:
            logger.error(f"Failed to fetch versions from Mojang: {e}")
            return []

    def get_installed_versions(self) -> List[Dict[str, str]]:
        """Возвращает список установленных версий."""
        installed = []
        versions_dir = self.minecraft_dir / "versions"
        if not versions_dir.exists():
            return installed

        for path in versions_dir.iterdir():
            if path.is_dir() and (path / f"{path.name}.jar").exists():
                installed.append({
                    "id": path.name,
                    "type": "local",
                    "release_time": ""
                })
        return installed

    def is_version_installed(self, version_id: str) -> bool:
        """Проверяет, установлена ли версия Minecraft."""
        version_dir = self.minecraft_dir / "versions" / version_id
        jar_file = version_dir / f"{version_id}.jar"
        return jar_file.exists()

    def install_version(self, version_id: str) -> None:
        """Устанавливает версию Minecraft с отслеживанием прогресса."""
        logger.info(f"Installing Minecraft {version_id}")
        
        def callback(progress: int, total: int, task: str):
            if total > 0:
                percent = (progress / total) * 100
                logger.info(f"[{version_id}] {task}: {percent:.1f}%")

        try:
            mll.install.install_minecraft_version(
                version_id,
                str(self.minecraft_dir),
                callback=callback
            )
            logger.info(f"Minecraft {version_id} installed successfully")
        except Exception as e:
            logger.error(f"Failed to install Minecraft {version_id}: {e}")
            raise

    def install_forge(self, version_id: str) -> None:
        """Устанавливает Forge для версии с проверкой зависимостей."""
        logger.info(f"Installing Forge for {version_id}")
        forge_version = mll.forge.find_forge_version(version_id)
        if forge_version is None:
            raise RuntimeError(f"Forge not found for {version_id}")

        # Устанавливаем базовую версию, если нужно
        base_version = forge_version.split('-')[0]
        if base_version != version_id and not self.is_version_installed(base_version):
            self.install_version(base_version)

        mll.forge.install_forge_version(forge_version, str(self.minecraft_dir))
        logger.info(f"Forge {forge_version} installed")

    def install_fabric(self, version_id: str) -> None:
        """Устанавливает Fabric для версии с проверкой зависимостей."""
        logger.info(f"Installing Fabric for {version_id}")

        # Проверяем базовую версию
        if not self.is_version_installed(version_id):
            self.install_version(version_id)

        mll.fabric.install_fabric(version_id, str(self.minecraft_dir))
        logger.info(f"Fabric installed for {version_id}")

    def get_java_executable(self) -> Optional[str]:
        """Возвращает путь к Java с приоритетом пользовательского выбора."""
        # Сначала пробуем из библиотеки
        java = mll.utils.get_java_executable()
        if java and Path(java).exists():
            return java

        # Затем ищем в PATH
        java_path = shutil.which("java")
        if java_path:
            return java_path

        # Для Windows можно попробовать стандартные пути
        if os.name == 'nt':
            possible_paths = [
                r"C:\Program Files\Java\*\bin\java.exe",
                r"C:\Program Files (x86)\Java\*\bin\java.exe"
            ]
            for path_pattern in possible_paths:
                matches = glob.glob(path_pattern)
                if matches:
                    return matches[0]

        return None

    def launch(
        self,
        version_id: str,
        username: str,
        uuid: str = "",
        access_token: str = "",
        java_path: str = "",
        max_memory: int = 4096,
        min_memory: int = 512,
        width: int = 1280,
        height: int = 720,
        fullscreen: bool = False,
        server: str = "",
        port: int = 25565,
    ) -> subprocess.Popen:
        """Запускает Minecraft и возвращает процесс."""
        logger.debug(f"Launching Minecraft {version_id} as {username}")

        # Проверяем и устанавливаем версию
        if not self.is_version_installed(version_id):
            logger.info(f"Version {version_id} not installed, installing...")
            self.install_version(version_id)

        # Получаем путь к Java
        if not java_path:
            java_path = self.get_java_executable()
            if not java_path:
                raise RuntimeError("Java executable not found")

        options = {
            "username": username,
            "uuid": uuid or "0" * 32,
            "token": access_token or "0" * 32,
            "jvmArguments": [
                f"-Xms{min_memory}M",
                f"-Xmx{max_memory}M",
                "-Djava.net.preferIPv4Stack=true"  # Улучшает сетевое подключение
            ],
            "gameResolution": [width, height] if not fullscreen else [],
            "fullscreen": fullscreen,
            "server": server,
            "port": str(port),
            "executablePath": java_path  # Явно указываем путь к Java
        }

        try:
            command = mll.command.get_minecraft_command(
                version_id, str(self.minecraft_dir), options
            )
        except Exception as e:
            logger.error(f"Failed to generate command for {version_id}: {e}")
            raise

        logger.debug(f"Full command: {' '.join(str(c) for c in command)}")

        # Запускаем с улучшенной обработкой ошибок
        error_log = self.minecraft_dir / "latest.log"
        with open(error_log, "w", encoding="utf-8") as err_file:
            process = subprocess.Popen(
                command,
                cwd=str(self.minecraft_dir),
                stdout=err_file,
                stderr=subprocess.STDOUT,  # Перенаправляем stderr в stdout
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )

        logger.info(f"Minecraft started, pid={process.pid}, logs: {error_log}")
        return process
