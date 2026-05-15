"""Страница модпаков на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QHBoxLayout, QLineEdit, QMessageBox,
    QComboBox, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient
from frontend.services.modpacks_api import ModpacksAPI


class SearchModpacksWorker(QThread):
    finished = pyqtSignal(list, int)
    error = pyqtSignal(str)

    def __init__(self, api: ModpacksAPI, query: str, game_version: str = ""):
        super().__init__()
        self.api = api
        self.query = query
        self.game_version = game_version

    def run(self):
        import asyncio
        try:
            result = asyncio.run(
                self.api.search(self.query, self.game_version, limit=20)
            )
            self.finished.emit(result.get("results", []), result.get("total", 0))
        except Exception as e:
            self.error.emit(str(e))


class InstallModpackWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: ModpacksAPI, project_id: str, new_name: str):
        super().__init__()
        self.api = api
        self.project_id = project_id
        self.new_name = new_name

    def run(self):
        import asyncio
        try:
            result = asyncio.run(
                self.api.install(self.project_id, new_name=self.new_name)
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ModpacksPage(QWidget):
    """Страница модпаков."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.modpacks_api = ModpacksAPI(self.api_client)
        self._create_ui()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("📦 Модпаки")
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

        # Поиск + фильтр
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск модпаков...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        self.search_input.returnPressed.connect(self._search_modpacks)
        search_layout.addWidget(self.search_input, 1)

        self.version_combo = QComboBox()
        self.version_combo.addItems(["Все версии", "1.20.4", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"])
        self.version_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        search_layout.addWidget(self.version_combo)

        search_btn = QPushButton("🔍 Найти")
        search_btn.setFixedHeight(34)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #4a6a90; }
        """)
        search_btn.clicked.connect(self._search_modpacks)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # Результаты
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

    def _search_modpacks(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Поиск", "Введите поисковый запрос")
            return
        version = self.version_combo.currentText()

        self._clear_results()
        loading = QLabel("Поиск модпаков...")
        loading.setStyleSheet("color: #a0a0a0; padding: 20px;")
        self.scroll_layout.addWidget(loading)

        self.worker = SearchModpacksWorker(
            self.modpacks_api, query,
            game_version=version if version != "Все версии" else ""
        )
        self.worker.finished.connect(self._on_results)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _clear_results(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_results(self, results: list, total: int):
        self._clear_results()
        if not results:
            empty = QLabel("Модпаки не найдены")
            empty.setStyleSheet("color: #a0a0a0; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty)
        else:
            info = QLabel(f"🔍 Найдено: {total}")
            info.setStyleSheet("color: #a0a0a0; font-size: 12px; padding: 10px 0;")
            self.scroll_layout.addWidget(info)
            for mp in results:
                self._add_modpack_card(mp)
        self.scroll_layout.addStretch()

    def _add_modpack_card(self, mp: dict):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a35;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)

        title = QLabel(mp.get("title", mp.get("slug", "?")))
        title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        card_layout.addWidget(title)

        desc = QLabel(mp.get("description", "")[:150] + "...")
        desc.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        meta = QLabel(f"⬇ {mp.get('downloads', 0):,} • {', '.join(mp.get('game_versions', [])[:3])}")
        meta.setStyleSheet("color: #808080; font-size: 11px;")
        card_layout.addWidget(meta)

        install_btn = QPushButton("📦 Установить")
        install_btn.setFixedHeight(28)
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        install_btn.clicked.connect(lambda: self._install_modpack(mp))
        card_layout.addWidget(install_btn)

        self.scroll_layout.addWidget(card)

    def _install_modpack(self, modpack: dict):
        project_id = modpack.get("project_id" or modpack.get("id", ""))
        if not project_id:
            QMessageBox.warning(self, "Ошибка", "ID модпака не найден")
            return

        new_name, ok = QInputDialog.getText(
            self, "Установка модпака",
            f"Название инстанса для {modpack.get('title', 'modpack')}:",
            text=modpack.get("title", "modpack")
        )
        if not ok or not new_name:
            return

        self.install_worker = InstallModpackWorker(self.modpacks_api, project_id, new_name)
        self.install_worker.finished.connect(lambda r: QMessageBox.information(
            self, "Готово", f"Модпак установлен!\nИнстанс: {r.get('instance', {}).get('name', '?')}"
        ))
        self.install_worker.error.connect(lambda e: QMessageBox.critical(self, "Ошибка", str(e)))
        self.install_worker.start()

    def _on_error(self, msg: str):
        QMessageBox.critical(self, "Ошибка", msg)
