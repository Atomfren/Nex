"""Страница AI чата на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

import websocket
import json


class AIChatMessage(QFrame):
    """Сообщение в чате."""

    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)
        self.setStyleSheet("""
            QFrame {
                background-color: %s;
                border-radius: 10px;
                padding: 10px;
            }
        """ % ("#3a5a80" if is_user else "#2a2a35"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        self.message_label = QLabel(text)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

    def set_text(self, text: str):
        self.message_label.setText(text)


class AIWebSocketWorker(QThread):
    """Рабочий поток для WebSocket соединения с AI."""

    token_received = pyqtSignal(str)
    message_done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, message: str):
        super().__init__()
        self.message = message
        self._running = True

    def run(self):
        """Подключается к WebSocket и получает стриминговый ответ."""
        try:
            ws = websocket.create_connection("ws://127.0.0.1:8000/api/v1/ai/chat")
            ws.send(json.dumps({"text": self.message}))

            full_text = ""
            while self._running:
                try:
                    data = json.loads(ws.recv())
                    if "error" in data:
                        self.error.emit(data["error"])
                        break
                    if data.get("done"):
                        self.message_done.emit()
                        break
                    if "token" in data:
                        full_text += data["token"]
                        self.token_received.emit(full_text)
                except websocket.WebSocketConnectionClosedException:
                    break
            ws.close()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._running = False


class AIChatPage(QWidget):
    """Страница AI чата."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_ai_msg = None
        self._create_ui()

    def _create_ui(self):
        """Создаёт UI элементы."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QVBoxLayout(header)

        title = QLabel("🤖 AI Помощник")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)

        main_layout.addWidget(header)

        # Область чата
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #3a3a45;
                border-radius: 10px;
                background-color: #1e1e28;
            }
        """)

        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(10)

        # Приветственное сообщение
        welcome = AIChatMessage(
            "Привет! Я AI помощник NexoraLauncher.\n\n"
            "Спроси меня о:\n"
            "• Как установить мод\n"
            "• Как создать инстанс\n"
            "• Оптимизация FPS\n"
            "• Настройка Java",
            is_user=False
        )
        self.chat_layout.addWidget(welcome)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_content)
        main_layout.addWidget(self.chat_scroll, 1)

        # Поле ввода
        input_layout = QHBoxLayout()

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Введите ваш вопрос...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("📤 Отправить")
        self.send_btn.setFixedWidth(120)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        main_layout.addLayout(input_layout)

    def _send_message(self):
        """Отправляет сообщение через WebSocket."""
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        # Добавляем сообщение пользователя
        user_msg = AIChatMessage(text, is_user=True)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, user_msg)
        self.input_field.clear()

        # Создаём пустое сообщение AI для стриминга
        self._current_ai_msg = AIChatMessage("", is_user=False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._current_ai_msg)

        # Запускаем WebSocket worker
        self.ws_worker = AIWebSocketWorker(text)
        self.ws_worker.token_received.connect(self._on_token)
        self.ws_worker.message_done.connect(self._on_done)
        self.ws_worker.error.connect(self._on_error)
        self.ws_worker.start()

    def _on_token(self, text: str):
        if self._current_ai_msg:
            self._current_ai_msg.set_text(text)
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )

    def _on_done(self):
        self._current_ai_msg = None

    def _on_error(self, msg: str):
        if self._current_ai_msg:
            self._current_ai_msg.set_text(f"Ошибка: {msg}")
            self._current_ai_msg = None
