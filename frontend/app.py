"""Главное окно NexoraLauncher на PyQt6."""

import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel, QPushButton, QScrollArea,
    QStatusBar, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from frontend.pages.home_page import HomePage
from frontend.pages.instances_page import InstancesPage
from frontend.pages.versions_page import VersionsPage
from frontend.pages.mods_page import ModsPage
from frontend.pages.modpacks_page import ModpacksPage
from frontend.pages.maps_page import MapsPage
from frontend.pages.resourcepacks_page import ResourcepacksPage
from frontend.pages.shaders_page import ShadersPage
from frontend.pages.servers_page import ServersPage
from frontend.pages.ai_chat_page import AIChatPage
from frontend.pages.settings_page import SettingsPage
from frontend.services.api_client import APIClient
from frontend.utils.logger import logger


class SidebarButton(QPushButton):
    """Кнопка боковой панели."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0a0a0;
                border: none;
                text-align: left;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a3a45;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #3a5a80;
                color: #80b3ff;
                font-weight: bold;
            }
        """)


class Sidebar(QFrame):
    """Боковая панель навигации."""

    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e28;
                border-radius: 15px;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Логотип
        logo_label = QLabel("Nexora\nLauncher")
        logo_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding: 20px 20px 10px 20px;
            }
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(logo_label)

        # Разделитель
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #3a3a45;")
        layout.addWidget(separator)

        # Кнопки навигации
        self.nav_buttons = {}
        nav_items = [
            ("home", "🏠  Главная"),
            ("instances", "📁  Инстансы"),
            ("versions", "📦  Версии"),
            ("mods", "🧩  Моды"),
            ("modpacks", "📦  Модпаки"),
            ("maps", "🗺️  Карты"),
            ("resourcepacks", "🎨  Ресурспаки"),
            ("shaders", "🌈  Шейдеры"),
            ("servers", "🖥️  Сервера"),
            ("ai", "🤖  AI Помощник"),
            ("settings", "⚙️  Настройки"),
        ]

        for page_id, label in nav_items:
            btn = SidebarButton(label)
            btn.setProperty("page_id", page_id)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_button_click(pid))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Версия
        version_label = QLabel("v0.1.0")
        version_label.setStyleSheet("color: gray; font-size: 11px; padding: 10px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        author_label = QLabel("Created by atomfren")
        author_label.setStyleSheet("color: gray; font-size: 10px; padding: 0px 0px 10px 0px;")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label)

    def _on_button_click(self, page_id: str):
        """Обработчик нажатия кнопки."""
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        self.page_changed.emit(page_id)

    def set_active_button(self, page_id: str):
        """Устанавливает активную кнопку."""
        if page_id in self.nav_buttons:
            self.nav_buttons[page_id].setChecked(True)


class ContentArea(QFrame):
    """Область контента."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #282832;
                border-radius: 15px;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # Stacked widget для страниц
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")

        # Страницы
        self.pages = {
            "home": HomePage(self),
            "instances": InstancesPage(self),
            "versions": VersionsPage(self),
            "mods": ModsPage(self),
            "modpacks": ModpacksPage(self),
            "maps": MapsPage(self),
            "resourcepacks": ResourcepacksPage(self),
            "shaders": ShadersPage(self),
            "servers": ServersPage(self),
            "ai": AIChatPage(self),
            "settings": SettingsPage(self),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        layout.addWidget(self.stack)

    def get_api_client(self):
        """Возвращает API клиент для страниц."""
        return self.parent().api_client if self.parent() else None

    def show_page(self, page_id: str):
        """Показывает указанную страницу."""
        if page_id in self.pages:
            self.stack.setCurrentWidget(self.pages[page_id])


class NexoraLauncherApp(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        logger.info("Initializing NexoraLauncherApp")
        self.setWindowTitle("NexoraLauncher")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        # API клиент
        self.api_client = APIClient(base_url="http://127.0.0.1:8000/api/v1")
        logger.debug(f"APIClient initialized with base_url={self.api_client.base_url}")

        # Настройка стиля
        self._setup_styles()

        # Центральная виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Верхняя часть (sidebar + content)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # Боковая панель
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        top_layout.addWidget(self.sidebar)

        # Область контента
        self.content_area = ContentArea()
        top_layout.addWidget(self.content_area, 1)

        main_layout.addLayout(top_layout)

        # Статус бар
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #23232d;
                color: #ffffff;
                padding: 5px;
                border-radius: 10px;
            }
        """)
        self.status_label = QLabel("Готов")
        self.status_bar.addPermanentWidget(self.status_label)
        main_layout.addWidget(self.status_bar)

        # Инициализация
        self.sidebar.set_active_button("home")
        self.content_area.show_page("home")
        logger.info("NexoraLauncherApp initialized successfully")

    def _setup_styles(self):
        """Настройка стилей приложения."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e28;
            }
        """)

    def _on_page_changed(self, page_id: str):
        """Обработчик изменения страницы."""
        logger.info(f"Page changed to: {page_id}")
        self.content_area.show_page(page_id)
        self.set_status(f"Страница: {page_id}")

    def set_status(self, text: str):
        """Устанавливает текст статус-бара."""
        self.status_label.setText(text)

    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        logger.info("Closing NexoraLauncherApp")
        import asyncio
        try:
            result = asyncio.run(self.api_client.close())
            logger.debug("API client closed")
        except Exception as e:
            logger.warning(f"Error closing API client: {e}")
        event.accept()
