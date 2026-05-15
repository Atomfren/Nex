# NexoraLauncher Architecture

## 📋 Оглавление

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [API Контракты](#api-контракты)
- [Запуск](#запуск)
- [План миграции](#план-миграции)
- [Документация](#документация)

---

## Обзор

NexoraLauncher — это лаунчер Minecraft следующего поколения с чётким разделением на backend и frontend компоненты.

### Ключевые особенности

- **Независимость UI**: Backend предоставляет REST API, что позволяет легко заменить GUI или добавить веб/мобильный клиент
- **Масштабируемость**: Backend можно масштабировать отдельно, добавлять кэширование, балансировку
- **Современный стек**: FastAPI, async/await, WebSocket для real-time коммуникации
- **Кроссплатформенность**: Один backend для Windows, Linux, macOS
- **PyQt6 UI**: Современный нативный GUI с профессиональным дизайном

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        NexoraLauncher                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Backend (FastAPI)                     │   │
│  │  REST API + WebSocket + Background Tasks                │   │
│  │  Business Logic + Data Access + External APIs           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ▲                                  │
│                              │ HTTP / WebSocket                  │
│  ┌───────────────────────────┴────────────────────────────────┐│
│  │                    Frontend (PyQt6)                         ││
│  │  GUI + API Clients + UI Components                         ││
│  └────────────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                      Shared Modules                        │ │
│  │  Config + Crypto + i18n + Paths                          │ │
│  └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Структура проекта

```
nexoralauncher/
├── ARCHITECTURE/                    # Документация архитектуры
│   ├── TECHNICAL_SPEC.md           # Полное техническое задание
│   ├── IMPLEMENTATION_SUMMARY.md   # Сводка реализации
│   └── QUICKSTART.md               # Быстрый старт
│
├── backend/                         # 🔧 Backend сервис (FastAPI)
│   ├── main.py                     # FastAPI приложение
│   ├── config.py                   # Конфигурация
│   ├── api/v1/                     # API Endpoints
│   │   ├── health.py               # Health check
│   │   ├── instances.py            # CRUD инстансов
│   │   ├── minecraft.py            # Запуск Minecraft
│   │   ├── mods.py                 # Моды (Modrinth)
│   │   ├── modpacks.py             # Модпаки
│   │   ├── auth.py                 # Авторизация
│   │   ├── ai.py                   # AI чат (WebSocket)
│   │   ├── settings.py             # Настройки
│   │   └── servers.py              # Сервера
│   ├── core/                       # Бизнес-логика
│   │   ├── auth.py                 # Аутентификация
│   │   ├── instance.py             # Инстансы
│   │   ├── minecraft.py            # Minecraft менеджер
│   │   ├── java_detector.py        # Детектор Java
│   │   ├── server_manager.py       # Менеджер серверов
│   │   ├── server_ping.py          # Ping серверов
│   │   └── pack_manager.py         # Экспорт/импорт
│   └── services/                   # Внешние сервисы
│       ├── ai_assistant.py         # Локальный LLM (llama.cpp)
│       └── modrinth_client.py      # Modrinth API клиент
│
├── frontend/                        # 🖥️ Frontend GUI (PyQt6)
│   ├── main.py                     # Точка входа
│   ├── app.py                      # Главное окно
│   ├── pages/                      # Страницы
│   └── services/                   # API клиенты
│
├── shared/                          # 📦 Общие модули
│   ├── config.py                   # Конфигурация
│   ├── crypto.py                   # Шифрование (Fernet)
│   ├── i18n.py                     # Локализация
│   └── paths.py                    # Пути
│
├── backend-requirements.txt         # Зависимости backend
├── frontend-requirements.txt        # Зависимости frontend
└── requirements.txt                 # Все зависимости
```

---

## API Контракты

### REST Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/instances/` | Список инстансов |
| POST | `/api/v1/instances/` | Создать инстанс |
| PATCH | `/api/v1/instances/{name}` | Обновить инстанс |
| DELETE | `/api/v1/instances/{name}` | Удалить инстанс |
| POST | `/api/v1/minecraft/launch` | Запустить Minecraft |
| GET | `/api/v1/minecraft/versions/available` | Доступные версии |
| POST | `/api/v1/mods/search` | Поиск модов |
| POST | `/api/v1/auth/offline/login` | Офлайн вход |
| GET | `/api/v1/settings/` | Настройки |

### WebSocket Endpoints

| Endpoint | Описание |
|----------|----------|
| `WS /api/v1/ai/chat` | AI чат с streaming |

### Документация API

После запуска backend доступна автодокументация:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Запуск

### Вариант 1: Единый запуск (рекомендуется)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python -m quantumlauncher
```

### Вариант 2: Раздельный запуск

```bash
# Запуск backend
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000

# Запуск frontend (в новом терминале)
cd frontend
python main.py
```

### Вариант 3: Development

```bash
# Backend с hot-reload
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
python main.py
```

---

## Статус реализации

Все компоненты реализованы:

- ✅ Backend API (FastAPI) — все endpoints
- ✅ Бизнес-логика (core) — инстансы, Minecraft, авторизация, сервера
- ✅ Сервисы — Modrinth клиент, локальный LLM (llama.cpp)
- ✅ Frontend (PyQt6) — все страницы с реальными API-вызовами
- ✅ Shared модули — конфиг, шифрование, пути, i18n
- ✅ WebSocket AI чат со стримингом
- ✅ Автоопределение Java
- ✅ Ping Minecraft серверов

---

## Документация

| Документ | Описание |
|----------|----------|
| [`TECHNICAL_SPEC.md`](ARCHITECTURE/TECHNICAL_SPEC.md) | Полное техническое задание |
| [`IMPLEMENTATION_SUMMARY.md`](ARCHITECTURE/IMPLEMENTATION_SUMMARY.md) | Сводка реализации |
| [`QUICKSTART.md`](ARCHITECTURE/QUICKSTART.md) | Быстрый старт |
| `backend/main.py` | FastAPI приложение |
| `backend/api/v1/*.py` | API endpoints |
| `frontend/app.py` | GUI приложение |

---

## Разработка

### Добавление нового endpoint

1. Создайте файл в `backend/api/v1/`
2. Определите Pydantic модели
3. Реализуйте endpoint функции
4. Добавьте в `backend/api/v1/__init__.py`
5. Подключите в `backend/main.py`

### Добавление новой страницы UI

1. Создайте файл в `frontend/pages/`
2. Наследуйтесь от `QWidget`
3. Используйте QThread для асинхронных API-запросов
4. Подключите в `frontend/app.py`

---

## Тестирование

```bash
# Backend unit tests
pytest backend/tests/

# Integration tests
pytest tests/integration/

# Frontend tests (требует дисплей)
pytest frontend/tests/
```

---

## Контакты

- **Архитектор**: NLP-Core-Team
- **Разработчик**: atomfren
- **Репозиторий**: https://github.com/atomfren/quantumlauncher

---

## Лицензия

MIT License
