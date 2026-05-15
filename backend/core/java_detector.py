"""Детектор установленных Java на системе."""

import os
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger


@dataclass
class JavaInfo:
    """Информация о Java."""
    path: str
    version: str
    vendor: str


def _run_java_version(java_path: Path) -> Optional[JavaInfo]:
    """Запускает java -version и парсит вывод."""
    try:
        result = subprocess.run(
            [str(java_path), "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="replace"
        )
        output = result.stderr or result.stdout
        version_match = re.search(r'(?:openjdk|java) version "([^"]+)"', output, re.IGNORECASE)
        version = version_match.group(1) if version_match else "unknown"
        vendor_match = re.search(r'([A-Za-z\s]+) Runtime Environment', output)
        vendor = vendor_match.group(1).strip() if vendor_match else "Unknown"
        return JavaInfo(path=str(java_path), version=version, vendor=vendor)
    except Exception:
        return None


def _scan_directory(directory: Path) -> List[JavaInfo]:
    """Сканирует директорию на наличие java.exe / java."""
    found = []
    if not directory.exists():
        return found

    executable = "java.exe" if os.name == "nt" else "java"
    for java_path in directory.rglob(executable):
        info = _run_java_version(java_path)
        if info:
            found.append(info)
    return found


def find_java_installations() -> List[JavaInfo]:
    """Находит все установки Java на системе."""
    java_paths: List[Path] = []

    if os.name == "nt":
        program_files = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")),
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Packages",
        ]
        for pf in program_files:
            java_paths.extend(pf.rglob("java.exe"))
            java_paths.extend(pf.rglob("javaw.exe"))
    else:
        linux_paths = [
            Path("/usr/lib/jvm"),
            Path("/usr/java"),
            Path("/opt"),
            Path.home() / ".sdkman" / "candidates" / "java",
        ]
        for lp in linux_paths:
            if lp.exists():
                for sub in lp.iterdir():
                    java_bin = sub / "bin" / "java"
                    if java_bin.exists():
                        java_paths.append(java_bin)

    results = []
    seen = set()
    for jp in java_paths:
        real = jp.resolve()
        if real not in seen:
            seen.add(real)
            info = _run_java_version(real)
            if info:
                results.append(info)

    # Также проверяем JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        exe = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if exe.exists():
            info = _run_java_version(exe.resolve())
            if info and info.path not in {r.path for r in results}:
                results.append(info)

    return sorted(results, key=lambda x: x.version, reverse=True)


def find_best_java(min_version: int = 17) -> Optional[JavaInfo]:
    """Находит лучшую подходящую Java (по умолчанию >= 17)."""
    candidates = find_java_installations()
    for java in candidates:
        try:
            major = int(java.version.split(".")[0])
            if major >= min_version:
                return java
        except ValueError:
            continue
    return candidates[0] if candidates else None
