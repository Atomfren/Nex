"""Управление экспортом/импортом инстансов (zip / mrpack)."""

import json
import shutil
import zipfile
from pathlib import Path
from typing import Optional

from loguru import logger

from shared.paths import get_instances_dir, get_cache_dir
from backend.core.instance import Instance


class PackManager:
    """Менеджер паков инстансов."""

    @staticmethod
    def export_instance(name: str, output_path: Optional[Path] = None) -> Path:
        """Экспортирует инстанс в ZIP архив."""
        instance = Instance.load(name)
        if instance is None:
            raise FileNotFoundError(f"Instance '{name}' not found")

        if output_path is None:
            output_path = get_cache_dir() / f"{name}.zip"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in instance.path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(instance.path)
                    zf.write(file_path, arcname)

        logger.info(f"Instance '{name}' exported to {output_path}")
        return output_path

    @staticmethod
    def import_zip(file_path: Path, new_name: str) -> Instance:
        """Импортирует инстанс из ZIP архива."""
        instances_dir = get_instances_dir()
        target_dir = instances_dir / new_name
        if target_dir.exists():
            raise FileExistsError(f"Instance '{new_name}' already exists")

        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(target_dir)

        instance = Instance.load(new_name)
        if instance is None:
            instance = Instance(name=new_name, version="unknown")
            instance.save()
        logger.info(f"Instance imported as '{new_name}'")
        return instance

    @staticmethod
    def import_mrpack(file_path: Path, new_name: str) -> Instance:
        """Импортирует инстанс из .mrpack (Modrinth modpack)."""
        instances_dir = get_instances_dir()
        target_dir = instances_dir / new_name
        if target_dir.exists():
            raise FileExistsError(f"Instance '{new_name}' already exists")

        target_dir.mkdir(parents=True, exist_ok=True)
        game_dir = target_dir / ".minecraft"
        game_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(file_path, "r") as zf:
            # Сначала ищем modrinth.index.json
            index_info = None
            for name in zf.namelist():
                if name.endswith("modrinth.index.json"):
                    index_info = json.loads(zf.read(name))
                    break

            # Извлекаем overrides
            for item in zf.infolist():
                if item.filename.startswith("overrides/"):
                    rel = item.filename[len("overrides/"):]
                    zf.extract(item, game_dir / rel)
                elif item.filename.startswith("client-overrides/"):
                    rel = item.filename[len("client-overrides/"):]
                    zf.extract(item, game_dir / rel)

        version = "unknown"
        mod_loader = "vanilla"
        loader_version = ""
        if index_info:
            dependencies = index_info.get("dependencies", {})
            if "minecraft" in dependencies:
                version = dependencies["minecraft"]
            if "forge" in dependencies:
                mod_loader = "forge"
                loader_version = dependencies["forge"]
            elif "fabric-loader" in dependencies:
                mod_loader = "fabric"
                loader_version = dependencies["fabric-loader"]
            elif "quilt-loader" in dependencies:
                mod_loader = "quilt"
                loader_version = dependencies["quilt-loader"]

        instance = Instance(
            name=new_name,
            version=version,
            mod_loader=mod_loader,
            loader_version=loader_version
        )
        instance.save()
        logger.info(f"Modpack imported as '{new_name}'")
        return instance
