"""Страница версий Minecraft на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QHBoxLayout, QMessageBox, QComboBox,
    QTabWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient
from frontend.services.minecraft_api import MinecraftAPI
from loguru import logger


class LoadVersionsWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: MinecraftAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        import traceback
        try:
            result = asyncio.run(self.api.get_available_versions())
            logger.info(f"LoadVersionsWorker: success, {len(result)} versions")
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{e}" if str(e) else traceback.format_exc()
            logger.error(f"LoadVersionsWorker error: {error_msg}")
            self.error.emit(error_msg)


class LoadInstalledVersionsWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: MinecraftAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        import traceback
        try:
            result = asyncio.run(self.api.get_installed_versions())
            logger.info(f"LoadInstalledVersionsWorker: success, {len(result)} installed")
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{e}" if str(e) else traceback.format_exc()
            logger.error(f"LoadInstalledVersionsWorker error: {error_msg}")
            self.error.emit(error_msg)


class InstallVersionWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: MinecraftAPI, version_id: str):
        super().__init__()
        self.api = api
        self.version_id = version_id

    def run(self):
        import asyncio
        import traceback
        try:
            result = asyncio.run(self.api.install_version(self.version_id))
            logger.info(f"InstallVersionWorker: success, {self.version_id}")
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{e}" if str(e) else traceback.format_exc()
            logger.error(f"InstallVersionWorker error for {self.version_id}: {error_msg}")
            self.error.emit(error_msg)            


class VersionsPage(QWidget):
    """Страница версий Minecraft."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.minecraft_api = MinecraftAPI(self.api_client)
        self._create_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_versions()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("📦 Версии Minecraft")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover { background-color: #4a6a90; }
        """)
        refresh_btn.clicked.connect(self._load_versions)
        header_layout.addWidget(refresh_btn)

        layout.addWidget(header)

        # Фильтр типа версии
        filter_layout = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Все", "release", "snapshot", "old_beta", "old_alpha"])
        self.type_filter.setStyleSheet("""
            QComboBox {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)
        self.type_filter.currentTextChanged.connect(self._apply_filter)
        filter_layout.addWidget(QLabel("Тип:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Табы для доступных и установленных
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: transparent; }
            QTabBar::tab {
                background-color: #2a2a35;
                color: #a0a0a0;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QTabBar::tab:selected { background-color: #3a5a80; color: #ffffff; }
        """)

        # Вкладка доступных версий
        self.available_scroll = self._create_scroll_area()
        self.available_layout = QVBoxLayout(self.available_scroll.widget())
        self.available_layout.setContentsMargins(0, 0, 0, 0)
        self.available_layout.setSpacing(6)
        self.tabs.addTab(self.available_scroll, "📥 Доступные")

        # Вкладка установленных версий
        self.installed_scroll = self._create_scroll_area()
        self.installed_layout = QVBoxLayout(self.installed_scroll.widget())
        self.installed_layout.setContentsMargins(0, 0, 0, 0)
        self.installed_layout.setSpacing(6)
        self.tabs.addTab(self.installed_scroll, "✅ Установленные")

        layout.addWidget(self.tabs)

    def _create_scroll_area(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        content = QWidget()
        scroll.setWidget(content)
        return scroll

    def _load_versions(self):
        """Загружает список версий."""
        self._clear_available()
        loading = QLabel("Загрузка версий...")
        loading.setStyleSheet("color: #a0a0a0; padding: 20px;")
        self.available_layout.addWidget(loading)

        self.worker = LoadVersionsWorker(self.minecraft_api)
        self.worker.finished.connect(self._on_versions_loaded)
        self.worker.error.connect(self._on_error)
        self.worker.start()

        # Также загружаем установленные
        self._load_installed()

    def _load_installed(self):
        self._clear_installed()
        self.installed_worker = LoadInstalledVersionsWorker(self.minecraft_api)
        self.installed_worker.finished.connect(self._on_installed_loaded)
        self.installed_worker.error.connect(lambda _: None)
        self.installed_worker.start()

    def _clear_available(self):
        while self.available_layout.count():
            item = self.available_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_installed(self):
        while self.installed_layout.count():
            item = self.installed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_versions_loaded(self, versions: list):
        self.all_versions = versions
        self._apply_filter()

    def _apply_filter(self):
        self._clear_available()
        if not hasattr(self, 'all_versions'):
            return

        filter_type = self.type_filter.currentText()
        filtered = self.all_versions
        if filter_type != "Все":
            filtered = [v for v in self.all_versions if v.get("type") == filter_type]

        if not filtered:
            empty = QLabel("Версии не найдены")
            empty.setStyleSheet("color: #a0a0a0; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.available_layout.addWidget(empty)
        else:
            for v in filtered[:50]:
                self._add_version_row(v, self.available_layout)
        self.available_layout.addStretch()

    def _on_installed_loaded(self, versions: list):
        self._clear_installed()
        if not versions:
            empty = QLabel("Нет установленных версий")
            empty.setStyleSheet("color: #a0a0a0; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.installed_layout.addWidget(empty)
        else:
            for v in versions:
                self._add_version_row(v, self.installed_layout, installed=True)
        self.installed_layout.addStretch()

    def _add_version_row(self, version: dict, layout, installed: bool = False):
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: #2a2a35;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        row_layout = QHBoxLayout(row)

        name = QLabel(version.get("id", "?"))
        name.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        row_layout.addWidget(name)

        vtype = QLabel(version.get("type", "?"))
        color = {"release": "#2ecc71", "snapshot": "#f39c12", "old_beta": "#e74c3c", "old_alpha": "#9b59b6"}
        vtype.setStyleSheet(f"color: {color.get(version.get('type'), '#a0a0a0')}; font-size: 12px;")
        row_layout.addWidget(vtype)
        row_layout.addStretch()

        if installed:
            lbl = QLabel("✅ Установлена")
            lbl.setStyleSheet("color: #2ecc71; font-size: 12px;")
            row_layout.addWidget(lbl)
        else:
            install_btn = QPushButton("⬇ Установить")
            install_btn.setFixedHeight(28)
            install_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a5a80;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    padding: 0 10px;
                }
                QPushButton:hover { background-color: #4a6a90; }
            """)
            install_btn.clicked.connect(lambda: self._install_version(version.get("id", "")))
            row_layout.addWidget(install_btn)

        layout.addWidget(row)

    def _install_version(self, version_id: str):
        reply = QMessageBox.question(
            self, "Установка",
            f"Установить Minecraft {version_id}?\nЭто может занять несколько минут.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.install_worker = InstallVersionWorker(self.minecraft_api, version_id)
        self.install_worker.finished.connect(lambda r: QMessageBox.information(
            self, "Готово", f"{r.get('status', 'OK')}: {r.get('version', version_id)}"
        ))
        self.install_worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
        self.install_worker.start()

    def _on_error(self, msg: str):
        QMessageBox.critical(self, "Ошибка", msg)
