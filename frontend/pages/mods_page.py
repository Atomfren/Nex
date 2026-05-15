"""Страница модов на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QHBoxLayout, QLineEdit, QMessageBox,
    QComboBox, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient
from frontend.services.mods_api import ModsAPI


class SearchModsWorker(QThread):
    finished = pyqtSignal(list, int)
    error = pyqtSignal(str)

    def __init__(self, api: ModsAPI, query: str, game_version: str = "", loader: str = ""):
        super().__init__()
        self.api = api
        self.query = query
        self.game_version = game_version
        self.loader = loader

    def run(self):
        import asyncio
        try:
            result = asyncio.run(
                self.api.search(self.query, self.game_version, self.loader, limit=20)
            )
            self.finished.emit(result.get("results", []), result.get("total", 0))
        except Exception as e:
            self.error.emit(str(e))


class FeaturedModsWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: ModsAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.get_featured(limit=12))
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DownloadModWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: ModsAPI, project_id: str, game_version: str = "", loader: str = ""):
        super().__init__()
        self.api = api
        self.project_id = project_id
        self.game_version = game_version
        self.loader = loader

    def run(self):
        import asyncio
        try:
            result = asyncio.run(
                self.api.download(self.project_id, self.game_version, self.loader)
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ModsPage(QWidget):
    """Страница модов."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.mods_api = ModsAPI(self.api_client)
        self._create_ui()

    def showEvent(self, event):
        """Загружает популярные моды при показе страницы."""
        super().showEvent(event)
        self._load_featured()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("🧩 Моды")
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

        # Поиск + фильтры
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск модов...")
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
        self.search_input.returnPressed.connect(self._search_mods)
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

        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["Все загрузчики", "forge", "fabric", "quilt"])
        self.loader_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        search_layout.addWidget(self.loader_combo)

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
        search_btn.clicked.connect(self._search_mods)
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

    def _load_featured(self):
        """Загружает популярные моды."""
        self._clear_results()
        loading = QLabel("Загрузка популярных модов...")
        loading.setStyleSheet("color: #a0a0a0; padding: 20px;")
        self.scroll_layout.addWidget(loading)

        self.worker = FeaturedModsWorker(self.mods_api)
        self.worker.finished.connect(self._on_featured)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _search_mods(self):
        """Ищет моды."""
        query = self.search_input.text().strip()
        if not query:
            return
        version = self.version_combo.currentText()
        loader = self.loader_combo.currentText()

        self._clear_results()
        loading = QLabel("Поиск...")
        loading.setStyleSheet("color: #a0a0a0; padding: 20px;")
        self.scroll_layout.addWidget(loading)

        self.worker = SearchModsWorker(
            self.mods_api, query,
            game_version=version if version != "Все версии" else "",
            loader=loader if loader != "Все загрузчики" else ""
        )
        self.worker.finished.connect(self._on_results)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _clear_results(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_featured(self, results: list):
        self._clear_results()
        if not results:
            empty = QLabel("Не удалось загрузить моды")
            empty.setStyleSheet("color: #a0a0a0; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty)
        else:
            title = QLabel("🔥 Популярные моды")
            title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold; padding: 10px 0;")
            self.scroll_layout.addWidget(title)
            for mod in results:
                self._add_mod_card(mod)
        self.scroll_layout.addStretch()

    def _on_results(self, results: list, total: int):
        self._clear_results()
        if not results:
            empty = QLabel("Моды не найдены")
            empty.setStyleSheet("color: #a0a0a0; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty)
        else:
            info = QLabel(f"🔍 Найдено: {total}")
            info.setStyleSheet("color: #a0a0a0; font-size: 12px; padding: 10px 0;")
            self.scroll_layout.addWidget(info)
            for mod in results:
                self._add_mod_card(mod)
        self.scroll_layout.addStretch()

    def _add_mod_card(self, mod: dict):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a35;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)

        top_layout = QHBoxLayout()
        title = QLabel(mod.get("title", mod.get("slug", "?")))
        title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        card_layout.addLayout(top_layout)

        desc = QLabel(mod.get("description", "")[:150] + "...")
        desc.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        meta = QLabel(f"⬇ {mod.get('downloads', 0):,} • {', '.join(mod.get('categories', [])[:3])}")
        meta.setStyleSheet("color: #808080; font-size: 11px;")
        card_layout.addWidget(meta)

        btn_layout = QHBoxLayout()
        download_btn = QPushButton("⬇ Скачать")
        download_btn.setFixedHeight(28)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        download_btn.clicked.connect(lambda: self._download_mod(mod))
        btn_layout.addWidget(download_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        self.scroll_layout.addWidget(card)

    def _download_mod(self, mod: dict):
        """Скачивает мод."""
        project_id = mod.get("project_id" or mod.get("id", ""))
        if not project_id:
            QMessageBox.warning(self, "Ошибка", "ID проекта не найден")
            return

        version = self.version_combo.currentText()
        loader = self.loader_combo.currentText()

        reply = QMessageBox.question(
            self, "Скачать мод",
            f"Скачать {mod.get('title', 'mod')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.download_worker = DownloadModWorker(
            self.mods_api, project_id,
            game_version=version if version != "Все версии" else "",
            loader=loader if loader != "Все загрузчики" else ""
        )
        self.download_worker.finished.connect(lambda r: QMessageBox.information(
            self, "Готово", f"Мод скачан:\n{r.get('path', '')}"
        ))
        self.download_worker.error.connect(lambda e: QMessageBox.critical(self, "Ошибка", str(e)))
        self.download_worker.start()

    def _on_error(self, msg: str):
        QMessageBox.critical(self, "Ошибка", msg)
