"""Страница серверов на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QHBoxLayout, QLineEdit, QMessageBox, QDialog, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient
from frontend.services.servers_api import ServersAPI


class LoadServersWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: ServersAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.list())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AddServerWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: ServersAPI, name: str, host: str, port: int):
        super().__init__()
        self.api = api
        self.name = name
        self.host = host
        self.port = port

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.create(self.name, self.host, self.port))
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DeleteServerWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, api: ServersAPI, server_id: str):
        super().__init__()
        self.api = api
        self.server_id = server_id

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.delete(self.server_id))
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class PingServerWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: ServersAPI, server_id: str):
        super().__init__()
        self.api = api
        self.server_id = server_id

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.ping(self.server_id))
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ConnectServerWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: ServersAPI, server_id: str):
        super().__init__()
        self.api = api
        self.server_id = server_id

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.connect(self.server_id))
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ServersPage(QWidget):
    """Страница серверов."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.servers_api = ServersAPI(self.api_client)
        self._create_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_servers()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("🖥️ Сервера")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_btn = QPushButton("➕ Добавить")
        add_btn.setFixedHeight(32)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover { background-color: #4a6a90; }
        """)
        add_btn.clicked.connect(self._show_add_dialog)
        header_layout.addWidget(add_btn)
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

    def _load_servers(self):
        self._clear_list()
        self.worker = LoadServersWorker(self.servers_api)
        self.worker.finished.connect(self._on_servers_loaded)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
        self.worker.start()

    def _clear_list(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_servers_loaded(self, servers: list):
        self._clear_list()
        if not servers:
            empty = QLabel("Нет добавленных серверов")
            empty.setStyleSheet("color: #a0a0a0; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty)
        else:
            for s in servers:
                self._add_server_card(s)
        self.scroll_layout.addStretch()

    def _add_server_card(self, server: dict):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a35;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)

        top = QHBoxLayout()
        name = QLabel(server.get("name", "?"))
        name.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        top.addWidget(name)
        top.addStretch()

        connect_btn = QPushButton("▶ Подключиться")
        connect_btn.setFixedHeight(26)
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 0 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        connect_btn.clicked.connect(lambda: self._connect_server(server.get("id", "")))
        top.addWidget(connect_btn)

        ping_btn = QPushButton("📡 Ping")
        ping_btn.setFixedHeight(26)
        ping_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 0 8px;
                font-size: 11px;
            }
        """)
        ping_btn.clicked.connect(lambda: self._ping_server(server.get("id", ""), status_lbl))
        top.addWidget(ping_btn)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(30, 26)
        del_btn.setStyleSheet("color: #ff6666; border: none;")
        del_btn.clicked.connect(lambda: self._delete_server(server.get("id", "")))
        top.addWidget(del_btn)
        card_layout.addLayout(top)

        addr = QLabel(f"{server.get('host', '?')}:{server.get('port', 25565)}")
        addr.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        card_layout.addWidget(addr)

        status_lbl = QLabel("Статус: неизвестно")
        status_lbl.setStyleSheet("color: #808080; font-size: 11px;")
        card_layout.addWidget(status_lbl)

        self.scroll_layout.addWidget(card)

    def _ping_server(self, server_id: str, label: QLabel):
        label.setText("Проверка...")
        self.ping_worker = PingServerWorker(self.servers_api, server_id)
        self.ping_worker.finished.connect(lambda r: label.setText(
            f"🟢 Онлайн: {r.get('player_count', 0)}/{r.get('max_players', 0)} • {r.get('latency_ms', 0)}ms"
            if r.get("online") else "🔴 Оффлайн"
        ))
        self.ping_worker.error.connect(lambda e: label.setText(f"Ошибка: {e}"))
        self.ping_worker.start()

    def _connect_server(self, server_id: str):
        reply = QMessageBox.question(
            self, "Подключение",
            "Запустить Minecraft и подключиться к серверу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.connect_worker = ConnectServerWorker(self.servers_api, server_id)
            self.connect_worker.finished.connect(
                lambda r: QMessageBox.information(
                    self, "Запущено",
                    f"Minecraft запущен\nPID: {r.get('pid', '?')}\nСервер: {r.get('server', '?')}:{r.get('port', 25565)}"
                )
            )
            self.connect_worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
            self.connect_worker.start()

    def _delete_server(self, server_id: str):
        reply = QMessageBox.question(self, "Подтверждение", "Удалить сервер?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.del_worker = DeleteServerWorker(self.servers_api, server_id)
            self.del_worker.finished.connect(self._load_servers)
            self.del_worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
            self.del_worker.start()

    def _show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить сервер")
        dialog.setFixedSize(350, 220)
        dialog.setStyleSheet("QDialog { background-color: #1e1e28; }")
        dl = QVBoxLayout(dialog)

        name_in = QLineEdit()
        name_in.setPlaceholderText("Название")
        name_in.setStyleSheet("background-color: #2a2a35; color: #ffffff; border-radius: 6px; padding: 6px;")
        dl.addWidget(name_in)

        host_in = QLineEdit()
        host_in.setPlaceholderText("IP адрес или домен")
        host_in.setStyleSheet("background-color: #2a2a35; color: #ffffff; border-radius: 6px; padding: 6px;")
        dl.addWidget(host_in)

        port_in = QSpinBox()
        port_in.setRange(1, 65535)
        port_in.setValue(25565)
        port_in.setStyleSheet("color: #ffffff;")
        dl.addWidget(port_in)

        def do_add():
            self.add_worker = AddServerWorker(self.servers_api, name_in.text(), host_in.text(), port_in.value())
            self.add_worker.finished.connect(lambda _: (dialog.accept(), self._load_servers()))
            self.add_worker.error.connect(lambda msg: QMessageBox.critical(dialog, "Ошибка", msg))
            self.add_worker.start()

        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }
        """)
        add_btn.clicked.connect(do_add)
        dl.addWidget(add_btn)
        dialog.exec()
