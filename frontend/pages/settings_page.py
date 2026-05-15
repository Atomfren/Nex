"""Страница настроек на PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QHBoxLayout, QComboBox, QMessageBox, QSpinBox,
    QGroupBox, QFormLayout, QCheckBox, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from frontend.services.api_client import APIClient
from frontend.services.settings_api import SettingsAPI


class LoadSettingsWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: SettingsAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.get())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SaveSettingsWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: SettingsAPI, data: dict):
        super().__init__()
        self.api = api
        self.data = data

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.update(**self.data))
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DetectJavaWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: SettingsAPI):
        super().__init__()
        self.api = api

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self.api.detect_java())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SettingsPage(QWidget):
    """Страница настроек."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient()
        self.settings_api = SettingsAPI(self.api_client)
        self._create_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_settings()

    def _create_ui(self):
        """Создаёт UI элементы."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)

        title = QLabel("⚙️ Настройки")
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

        # Табы для категорий настроек
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

        # === Вкладка: Java и память ===
        java_tab = QWidget()
        java_layout = QVBoxLayout(java_tab)

        java_group = QGroupBox("☕ Java")
        java_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        java_form = QFormLayout(java_group)
        java_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.java_path = QLineEdit()
        self.java_path.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a35;
                color: #ffffff;
                border: 1px solid #3a3a45;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        java_path_layout = QHBoxLayout()
        java_path_layout.addWidget(self.java_path)
        browse_btn = QPushButton("📁 Обзор")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 10px;
            }
        """)
        browse_btn.clicked.connect(self._browse_java)
        java_path_layout.addWidget(browse_btn)
        java_form.addRow("Путь к Java:", java_path_layout)

        detect_btn = QPushButton("🔍 Автоопределение Java")
        detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a80;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #4a6a90; }
        """)
        detect_btn.clicked.connect(self._detect_java)
        java_form.addRow(detect_btn)

        # Список найденных Java
        self.java_list_label = QLabel("")
        self.java_list_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        self.java_list_label.setWordWrap(True)
        java_form.addRow(self.java_list_label)

        java_layout.addWidget(java_group)

        # Память
        mem_group = QGroupBox("🧠 Память")
        mem_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        mem_form = QFormLayout(mem_group)

        self.max_mem = QSpinBox()
        self.max_mem.setRange(512, 65536)
        self.max_mem.setSingleStep(512)
        self.max_mem.setSuffix(" MB")
        self.max_mem.setStyleSheet("color: #ffffff;")
        mem_form.addRow("Максимальная память:", self.max_mem)

        self.min_mem = QSpinBox()
        self.min_mem.setRange(256, 32768)
        self.min_mem.setSingleStep(256)
        self.min_mem.setSuffix(" MB")
        self.min_mem.setStyleSheet("color: #ffffff;")
        mem_form.addRow("Минимальная память:", self.min_mem)

        java_layout.addWidget(mem_group)
        java_layout.addStretch()
        self.tabs.addTab(java_tab, "☕ Java")

        # === Вкладка: Интерфейс ===
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)

        ui_group = QGroupBox("🎨 Внешний вид")
        ui_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        ui_form = QFormLayout(ui_group)

        self.appearance_mode = QComboBox()
        self.appearance_mode.addItems(["dark", "light"])
        self.appearance_mode.setStyleSheet("color: #ffffff;")
        ui_form.addRow("Тема:", self.appearance_mode)

        self.color_theme = QComboBox()
        self.color_theme.addItems(["blue", "green", "dark-blue"])
        self.color_theme.setStyleSheet("color: #ffffff;")
        ui_form.addRow("Цвет акцента:", self.color_theme)

        self.language = QComboBox()
        self.language.addItems(["ru", "en"])
        self.language.setStyleSheet("color: #ffffff;")
        ui_form.addRow("Язык:", self.language)

        self.fullscreen = QCheckBox("Запуск в полноэкранном режиме")
        self.fullscreen.setStyleSheet("color: #ffffff;")
        ui_form.addRow(self.fullscreen)

        ui_layout.addWidget(ui_group)

        # Разрешение
        res_group = QGroupBox("📐 Разрешение")
        res_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        res_form = QFormLayout(res_group)

        self.window_width = QSpinBox()
        self.window_width.setRange(800, 3840)
        self.window_width.setSingleStep(10)
        self.window_width.setStyleSheet("color: #ffffff;")
        res_form.addRow("Ширина окна:", self.window_width)

        self.window_height = QSpinBox()
        self.window_height.setRange(600, 2160)
        self.window_height.setSingleStep(10)
        self.window_height.setStyleSheet("color: #ffffff;")
        res_form.addRow("Высота окна:", self.window_height)

        ui_layout.addWidget(res_group)
        ui_layout.addStretch()
        self.tabs.addTab(ui_tab, "🎨 Интерфейс")

        # === Вкладка: JVM ===
        jvm_tab = QWidget()
        jvm_layout = QVBoxLayout(jvm_tab)

        jvm_group = QGroupBox("⚙️ JVM Профиль")
        jvm_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        jvm_form = QFormLayout(jvm_group)

        self.jvm_profile = QComboBox()
        self.jvm_profile.addItems(["default", "performance", "low"])
        self.jvm_profile.setStyleSheet("color: #ffffff;")
        jvm_form.addRow("Профиль:", self.jvm_profile)

        self.jvm_profile_desc = QLabel(
            "default - стандартные настройки\n"
            "performance - оптимизация для производительности\n"
            "low - минимальное потребление ресурсов"
        )
        self.jvm_profile_desc.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        self.jvm_profile_desc.setWordWrap(True)
        jvm_form.addRow(self.jvm_profile_desc)

        jvm_layout.addWidget(jvm_group)
        jvm_layout.addStretch()
        self.tabs.addTab(jvm_tab, "⚙️ JVM")

        layout.addWidget(self.tabs)

        # Кнопка сохранить
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить настройки")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        save_btn.clicked.connect(self._save_settings)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

    def _load_settings(self):
        self.worker = LoadSettingsWorker(self.settings_api)
        self.worker.finished.connect(self._on_settings_loaded)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
        self.worker.start()

    def _on_settings_loaded(self, settings: dict):
        self.java_path.setText(settings.get("java_path", ""))
        self.max_mem.setValue(settings.get("max_memory", 4096))
        self.min_mem.setValue(settings.get("min_memory", 512))
        self.jvm_profile.setCurrentText(settings.get("jvm_profile", "default"))
        self.language.setCurrentText(settings.get("language", "ru"))
        self.appearance_mode.setCurrentText(settings.get("appearance_mode", "dark"))
        self.color_theme.setCurrentText(settings.get("color_theme", "blue"))
        self.window_width.setValue(settings.get("window_width", 1200))
        self.window_height.setValue(settings.get("window_height", 800))
        self.fullscreen.setChecked(settings.get("fullscreen", False))

    def _save_settings(self):
        data = {
            "java_path": self.java_path.text(),
            "max_memory": self.max_mem.value(),
            "min_memory": self.min_mem.value(),
            "jvm_profile": self.jvm_profile.currentText(),
            "language": self.language.currentText(),
            "appearance_mode": self.appearance_mode.currentText(),
            "color_theme": self.color_theme.currentText(),
            "window_width": self.window_width.value(),
            "window_height": self.window_height.value(),
            "fullscreen": self.fullscreen.isChecked(),
        }
        self.save_worker = SaveSettingsWorker(self.settings_api, data)
        self.save_worker.finished.connect(lambda _: QMessageBox.information(self, "Успех", "Настройки сохранены"))
        self.save_worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
        self.save_worker.start()

    def _browse_java(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать Java executable", "",
            "Java (java.exe java);;Все файлы (*)"
        )
        if path:
            self.java_path.setText(path)

    def _detect_java(self):
        self.java_list_label.setText("Поиск Java...")
        self.detect_worker = DetectJavaWorker(self.settings_api)
        self.detect_worker.finished.connect(self._on_java_detected)
        self.detect_worker.error.connect(lambda e: QMessageBox.critical(self, "Ошибка", e))
        self.detect_worker.start()

    def _on_java_detected(self, java_list: list):
        if not java_list:
            self.java_list_label.setText("Java не найдена. Установите Java или укажите путь вручную.")
            QMessageBox.warning(self, "Java", "Java не найдена на системе")
            return

        info = "\n".join([f"• {j.get('version', '?')} ({j.get('vendor', '?')}) - {j.get('path', '')}" for j in java_list[:5]])
        self.java_list_label.setText(f"Найдено {len(java_list)} установок:\n{info}")
        self.java_path.setText(java_list[0].get("path", ""))
        QMessageBox.information(self, "Java найдена", f"Найдено {len(java_list)} установок Java. Выбрана: {java_list[0].get('version', '?')}")
