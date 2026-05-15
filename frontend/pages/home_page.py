"""Страница Home на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QPushButton,
    QHBoxLayout, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient


class LoadHomeDataWorker(QThread):
    finished = pyqtSignal(dict, list)
    error = pyqtSignal(str)

    def run(self):
        import asyncio
        try:
            client = APIClient()
            profile = asyncio.run(client.get("/auth/profile"))
            instances = asyncio.run(client.get("/instances/"))
            self.finished.emit(profile, instances)
        except Exception as e:
            self.error.emit(str(e))


class HomePage(QWidget):
    """Главная страница."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QVBoxLayout(header)
        
        self.title = QLabel("🏠 Главная")
        self.title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self.title)
        layout.addWidget(header)

        # Информация о профиле
        self.profile_frame = QFrame()
        self.profile_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a35;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        profile_layout = QVBoxLayout(self.profile_frame)
        self.profile_label = QLabel("Загрузка профиля...")
        self.profile_label.setStyleSheet("color: #a0a0a0; font-size: 14px;")
        profile_layout.addWidget(self.profile_label)
        layout.addWidget(self.profile_frame)

        # Быстрые действия
        actions = QFrame()
        actions.setStyleSheet("background-color: transparent;")
        actions_layout = QHBoxLayout(actions)

        self.play_btn = QPushButton("▶ Быстрый запуск")
        self.play_btn.setFixedHeight(42)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.play_btn.clicked.connect(self._quick_launch)
        actions_layout.addWidget(self.play_btn)

        self.create_btn = QPushButton("➕ Новый инстанс")
        self.create_btn.setFixedHeight(42)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4a6a90; }
        """)
        actions_layout.addWidget(self.create_btn)
        layout.addWidget(actions)

        # Последние инстансы
        recent_label = QLabel("📁 Ваши инстансы")
        recent_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; padding-top: 10px;")
        layout.addWidget(recent_label)

        self.instances_scroll = QScrollArea()
        self.instances_scroll.setWidgetResizable(True)
        self.instances_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.instances_content = QWidget()
        self.instances_layout = QVBoxLayout(self.instances_content)
        self.instances_layout.setContentsMargins(0, 0, 0, 0)
        self.instances_layout.setSpacing(8)
        self.instances_scroll.setWidget(self.instances_content)
        layout.addWidget(self.instances_scroll)
        layout.addStretch()

    def _load_data(self):
        self.worker = LoadHomeDataWorker()
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(lambda msg: self.profile_label.setText(f"Офлайн режим"))
        self.worker.start()

    def _on_data_loaded(self, profile: dict, instances: list):
        username = profile.get("username", "Игрок")
        auth_type = "Microsoft" if profile.get("auth_type") == "microsoft" else "Офлайн"
        self.profile_label.setText(f"👤 {username} • {auth_type}")

        while self.instances_layout.count():
            item = self.instances_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not instances:
            empty = QLabel("Нет инстансов. Создайте первый!")
            empty.setStyleSheet("color: #a0a0a0; padding: 20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.instances_layout.addWidget(empty)
        else:
            for inst in instances[:5]:
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a35;
                        border-radius: 8px;
                        padding: 8px;
                    }
                """)
                cl = QHBoxLayout(card)
                name = QLabel(inst.get("name", "?"))
                name.setStyleSheet("color: #ffffff; font-weight: bold;")
                cl.addWidget(name)
                ver = QLabel(f"{inst.get('mod_loader', '?')} {inst.get('version', '?')}")
                ver.setStyleSheet("color: #a0a0a0; font-size: 12px;")
                cl.addWidget(ver)
                cl.addStretch()
                self.instances_layout.addWidget(card)
        self.instances_layout.addStretch()

    def _quick_launch(self):
        QMessageBox.information(self, "Быстрый запуск", "Выберите инстанс на странице 'Инстансы'")
