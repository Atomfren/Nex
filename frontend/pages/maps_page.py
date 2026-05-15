"""Страница карт на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QPushButton,
    QHBoxLayout, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient
from frontend.services.instances_api import InstancesAPI


class LoadInstancesWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: InstancesAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.list())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MapsPage(QWidget):
    """Страница карт."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.instances_api = InstancesAPI(self.api_client)
        self._create_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_instances()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("🗺️ Карты")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # Выбор инстанса
        instance_layout = QHBoxLayout()
        instance_layout.addWidget(QLabel("Инстанс:"))
        self.instance_combo = QComboBox()
        self.instance_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)
        instance_layout.addWidget(self.instance_combo, 1)
        layout.addLayout(instance_layout)

        content = QLabel(
            "Управление картами\n\n"
            "• Установите карту, переместив файл .zip или .mcworld в папку saves инстанса\n"
            "• Или нажмите 'Открыть папку saves' для ручного управления"
        )
        content.setStyleSheet("""
            QLabel {
                color: #a0a0a0;
                font-size: 14px;
                padding: 20px;
            }
        """)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setWordWrap(True)
        layout.addWidget(content)

        open_btn = QPushButton("📂 Открыть папку saves")
        open_btn.setFixedHeight(36)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4a6a90; }
        """)
        open_btn.clicked.connect(self._open_saves)
        layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def _load_instances(self):
        self.worker = LoadInstancesWorker(self.instances_api)
        self.worker.finished.connect(self._on_instances_loaded)
        self.worker.error.connect(lambda _: None)
        self.worker.start()

    def _on_instances_loaded(self, instances: list):
        self.instance_combo.clear()
        if instances:
            for inst in instances:
                self.instance_combo.addItem(inst.get("name", "?"))
        else:
            self.instance_combo.addItem("Нет инстансов")

    def _open_saves(self):
        import os
        from shared.paths import get_instances_dir
        instance_name = self.instance_combo.currentText()
        if instance_name == "Нет инстансов":
            QMessageBox.warning(self, "Ошибка", "Сначала создайте инстанс")
            return
        path = get_instances_dir() / instance_name / ".minecraft" / "saves"
        path.mkdir(parents=True, exist_ok=True)
        if path.exists():
            os.startfile(str(path))
        else:
            QMessageBox.warning(self, "Ошибка", "Папка не найдена")
