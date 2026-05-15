"""Страница инстансов на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QDialog, QLineEdit,
    QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from frontend.services.instances_api import InstancesAPI
from frontend.services.minecraft_api import MinecraftAPI
from frontend.services.api_client import APIClient
from frontend.utils.logger import logger


class LoadInstancesWorker(QThread):
    """Рабочий поток для загрузки инстансов."""
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
            logger.error(f"LoadInstancesWorker error: {e}")
            self.error.emit(str(e))


class LoadOneInstanceWorker(QThread):
    """Рабочий поток для загрузки одного инстанса."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: InstancesAPI, name: str):
        super().__init__()
        self.api = api
        self.name = name

    def run(self):
        import asyncio
        import traceback
        try:
            result = asyncio.run(self.api.get(self.name))
            logger.info(f"LoadOneInstanceWorker: success, name={self.name}")
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{e}" if str(e) else traceback.format_exc()
            logger.error(f"LoadOneInstanceWorker error for '{self.name}': {error_msg}")
            self.error.emit(error_msg)


class CreateInstanceWorker(QThread):
    """Рабочий поток для создания инстанса."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: InstancesAPI, name: str, version: str, loader: str):
        super().__init__()
        self.api = api
        self.name = name
        self.version = version
        self.loader = loader

    def run(self):
        import asyncio
        import traceback
        try:
            result = asyncio.run(self.api.create(self.name, self.version, self.loader))
            logger.info(f"CreateInstanceWorker: success, name={self.name}")
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{e}" if str(e) else traceback.format_exc()
            logger.error(f"CreateInstanceWorker error for '{self.name}': {error_msg}")
            self.error.emit(error_msg)


class DeleteInstanceWorker(QThread):
    """Рабочий поток для удаления инстанса."""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, api: InstancesAPI, name: str):
        super().__init__()
        self.api = api
        self.name = name

    def run(self):
        import asyncio
        try:
            asyncio.run(self.api.delete(self.name))
            self.finished.emit()
        except Exception as e:
            logger.error(f"DeleteInstanceWorker error: {e}")
            self.error.emit(str(e))


class LaunchInstanceWorker(QThread):
    """Рабочий поток для запуска Minecraft."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: MinecraftAPI, version_id: str, username: str):
        super().__init__()
        self.api = api
        self.version_id = version_id
        self.username = username

    def run(self):
        import asyncio
        import traceback
        try:
            result = asyncio.run(self.api.launch(self.version_id, self.username))
            logger.info(f"LaunchInstanceWorker: success, result={result}")
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{e}" if str(e) else traceback.format_exc()
            logger.error(f"LaunchInstanceWorker error: {error_msg}")
            self.error.emit(error_msg)


class InstancesPage(QWidget):
    """Страница управления инстансами."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.instances_api = InstancesAPI(self.api_client)
        self.minecraft_api = MinecraftAPI(self.api_client)
        logger.info("InstancesPage initialized")
        self._create_ui()

    def showEvent(self, event):
        """Загружает инстансы при показе страницы."""
        super().showEvent(event)
        logger.debug("InstancesPage shown, loading instances...")
        self._load_instances()

    def _create_ui(self):
        """Создаёт UI элементы."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("📁 Инстансы")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.create_btn = QPushButton("➕ Создать")
        self.create_btn.setFixedWidth(120)
        self.create_btn.setFixedHeight(36)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a6a90;
            }
        """)
        self.create_btn.clicked.connect(self._show_create_dialog)
        header_layout.addWidget(self.create_btn)

        main_layout.addWidget(header)

        # Список инстансов
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(10)

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        # Загрузка инстансов произойдёт в showEvent

    def _clear_cards(self):
        """Очищает список карточек."""
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_instance_card(self, instance: dict):
        """Добавляет карточку инстанса."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a35;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        card_layout = QHBoxLayout(card)

        info = QFrame()
        info.setStyleSheet("background-color: transparent;")
        info_layout = QVBoxLayout(info)

        name_lbl = QLabel(instance.get("name", "Unknown"))
        name_lbl.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(name_lbl)

        meta_text = f"{instance.get('mod_loader', 'vanilla')} {instance.get('version', '?')} • Запусков: {instance.get('play_count', 0)}"
        meta = QLabel(meta_text)
        meta.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        info_layout.addWidget(meta)

        card_layout.addWidget(info)
        card_layout.addStretch()

        btns_layout = QHBoxLayout()

        play_btn = QPushButton("▶ Играть")
        play_btn.setFixedWidth(80)
        play_btn.setFixedHeight(28)
        play_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #1a5c3a;
                color: #808080;
            }
        """)
        play_btn.clicked.connect(lambda: self._launch_instance(instance.get("name", ""), play_btn))
        btns_layout.addWidget(play_btn)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(40, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff6666;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #cc4444;
            }
        """)
        del_btn.clicked.connect(lambda: self._delete_instance(instance.get("name", "")))
        btns_layout.addWidget(del_btn)

        btns_layout.setContentsMargins(10, 0, 0, 0)
        card_layout.addLayout(btns_layout)

        self.scroll_layout.addWidget(card)

    def _load_instances(self):
        """Загружает список инстансов с сервера."""
        logger.debug("Loading instances from API...")
        self._clear_cards()
        self.worker = LoadInstancesWorker(self.instances_api)
        self.worker.finished.connect(self._on_instances_loaded)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_instances_loaded(self, instances: list):
        """Обработчик загрузки инстансов."""
        logger.info(f"Loaded {len(instances)} instance(s)")
        self._clear_cards()
        if not instances:
            empty = QLabel("Нет созданных инстансов. Нажмите 'Создать' чтобы добавить.")
            empty.setStyleSheet("color: #a0a0a0; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty)
        else:
            for instance in instances:
                self._add_instance_card(instance)
        self.scroll_layout.addStretch()

    def _on_error(self, msg: str):
        """Обработчик ошибки."""
        logger.error(f"Instance page error: {msg}")
        QMessageBox.critical(self, "Ошибка", str(msg))

    def _delete_instance(self, name: str):
        """Удаляет инстанс."""
        logger.info(f"Requesting delete for instance '{name}'")
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить инстанс '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Deleting instance '{name}'")
            self.worker = DeleteInstanceWorker(self.instances_api, name)
            self.worker.finished.connect(self._load_instances)
            self.worker.error.connect(self._on_error)
            self.worker.start()

    def _launch_instance(self, name: str, btn: QPushButton = None):
        """Запускает Minecraft."""
        logger.info(f"Launching instance '{name}'")
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳")
        # Сначала получаем версию инстанса
        self.load_worker = LoadOneInstanceWorker(self.instances_api, name)
        self.load_worker.finished.connect(lambda inst: self._do_launch(inst, btn))
        self.load_worker.error.connect(lambda msg: self._on_launch_error(msg, btn))
        self.load_worker.start()

    def _do_launch(self, instance: dict, btn: QPushButton = None):
        """Запускает Minecraft с известной версией."""
        version = instance.get("version", "")
        name = instance.get("name", "Player")
        if not version:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить версию инстанса")
            if btn:
                btn.setEnabled(True)
                btn.setText("▶ Играть")
            return
        logger.info(f"Starting Minecraft {version} for instance '{name}'")
        self.launch_worker = LaunchInstanceWorker(self.minecraft_api, version, "Player")
        self.launch_worker.finished.connect(
            lambda r: self._on_launch_finished(r, name, btn)
        )
        self.launch_worker.error.connect(lambda msg: self._on_launch_error(msg, btn))
        self.launch_worker.start()

    def _on_launch_finished(self, response: dict, instance_name: str, btn: QPushButton = None):
        """Обработка результата запуска."""
        if btn:
            btn.setEnabled(True)
            btn.setText("▶ Играть")
        pid = response.get("pid")
        if not pid:
            error_detail = response.get("detail", "Неизвестная ошибка")
            logger.error(f"Failed to launch '{instance_name}': {error_detail}")
            QMessageBox.critical(self, "Ошибка запуска", f"Не удалось запустить Minecraft:\n{error_detail}")
            return
        logger.info(f"Instance '{instance_name}' launched, pid={pid}")
        QMessageBox.information(
            self, "Запущено",
            f"Minecraft запущен\nPID: {pid}\nВерсия: {response.get('version', '?')}"
        )

    def _on_launch_error(self, msg: str, btn: QPushButton = None):
        """Обработка ошибки запуска."""
        if btn:
            btn.setEnabled(True)
            btn.setText("▶ Играть")
        self._on_error(msg)

    def _show_create_dialog(self):
        """Показывает диалог создания инстанса."""
        logger.info("Opening create instance dialog")
        dialog = QDialog(self)
        dialog.setWindowTitle("Создать инстанс")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e28;
            }
        """)

        layout = QGridLayout(dialog)

        layout.addWidget(QLabel("Название:"), 0, 0)
        name_entry = QLineEdit()
        layout.addWidget(name_entry, 0, 1)

        layout.addWidget(QLabel("Версия Minecraft:"), 1, 0)
        version_entry = QLineEdit()
        version_entry.setPlaceholderText("1.20.1")
        layout.addWidget(version_entry, 1, 1)

        layout.addWidget(QLabel("Загрузчик:"), 2, 0)
        loader_combo = QComboBox()
        loader_combo.addItems(["vanilla", "forge", "fabric", "quilt"])
        layout.addWidget(loader_combo, 2, 1)

        def on_create():
            name = name_entry.text().strip()
            version = version_entry.text().strip()
            loader = loader_combo.currentText()

            if not name or not version:
                QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                return

            create_btn.setEnabled(False)
            create_btn.setText("Создание...")
            logger.info(f"Creating instance: name={name}, version={version}, loader={loader}")
            self.create_worker = CreateInstanceWorker(self.instances_api, name, version, loader)
            self.create_worker.finished.connect(
                lambda _: (dialog.accept(), self._load_instances())
            )
            self.create_worker.error.connect(
                lambda msg: (
                    create_btn.setEnabled(True),
                    create_btn.setText("Создать"),
                    logger.error(f"Failed to create instance '{name}': {msg}"),
                    QMessageBox.critical(dialog, "Ошибка", str(msg))
                )[-1]
            )
            self.create_worker.start()

        create_btn = QPushButton("Создать")
        create_btn.setFixedHeight(36)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        create_btn.clicked.connect(on_create)
        layout.addWidget(create_btn, 3, 0, 1, 2)

        dialog.exec()
        logger.debug("Create instance dialog closed")
