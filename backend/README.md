# NexoraLauncher Backend

Backend REST API сервис на FastAPI.

## Установка

```bash
pip install -r backend-requirements.txt
```

## Запуск

### Development режим

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Production режим

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Документация API

После запуска доступна автодокументация:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Структура

```
backend/
├── main.py                  # FastAPI приложение
├── config.py                # Конфигурация
├── api/v1/                  # API Endpoints
│   ├── health.py            # Health check
│   ├── instances.py         # CRUD инстансов
│   ├── minecraft.py         # Запуск Minecraft
│   ├── mods.py              # Моды (Modrinth)
│   ├── modpacks.py          # Модпаки
│   ├── auth.py              # Авторизация
│   ├── ai.py                # AI чат (WebSocket)
│   ├── settings.py          # Настройки
│   └── servers.py           # Сервера
├── core/                    # Бизнес-логика
│   ├── auth.py              # Аутентификация
│   ├── instance.py          # Инстансы
│   ├── minecraft.py         # Minecraft менеджер
│   ├── java_detector.py     # Детектор Java
│   ├── server_manager.py    # Менеджер серверов
│   ├── server_ping.py       # Ping серверов
│   └── pack_manager.py      # Экспорт/импорт
└── services/                # Внешние сервисы
    ├── ai_assistant.py      # Локальный LLM (llama.cpp)
    └── modrinth_client.py   # Modrinth API клиент
```

## API Endpoints

### Health
- `GET /api/v1/health` - Проверка работоспособности
- `GET /api/v1/ping` - Простой ping

### Instances
- `GET /api/v1/instances/` - Список инстансов
- `POST /api/v1/instances/` - Создать инстанс
- `GET /api/v1/instances/{name}` - Получить инстанс
- `PATCH /api/v1/instances/{name}` - Обновить инстанс
- `DELETE /api/v1/instances/{name}` - Удалить инстанс
- `POST /api/v1/instances/{name}/export` - Экспорт в ZIP
- `POST /api/v1/instances/import` - Импорт из ZIP/mrpack

### Minecraft
- `POST /api/v1/minecraft/launch` - Запустить Minecraft
- `GET /api/v1/minecraft/versions/available` - Доступные версии
- `GET /api/v1/minecraft/versions/installed` - Установленные версии
- `POST /api/v1/minecraft/versions/{version_id}/install` - Установить версию
- `POST /api/v1/minecraft/versions/{version_id}/install_forge` - Установить Forge
- `POST /api/v1/minecraft/versions/{version_id}/install_fabric` - Установить Fabric
- `GET /api/v1/minecraft/status/{process_id}` - Статус процесса
- `DELETE /api/v1/minecraft/stop/{process_id}` - Остановить процесс

### Mods
- `GET /api/v1/mods/search` - Поиск модов на Modrinth
- `GET /api/v1/mods/featured` - Популярные моды
- `GET /api/v1/mods/{project_id}` - Получить мод
- `GET /api/v1/mods/{project_id}/versions` - Версии мода
- `POST /api/v1/mods/download` - Скачать мод
- `POST /api/v1/mods/install` - Установить мод в инстанс
- `GET /api/v1/mods/installed` - Установленные моды
- `DELETE /api/v1/mods/uninstall` - Удалить мод

### Modpacks
- `GET /api/v1/modpacks/search` - Поиск модпаков
- `POST /api/v1/modpacks/install` - Установить модпак

### Auth
- `POST /api/v1/auth/offline/login` - Офлайн вход
- `POST /api/v1/auth/microsoft/login/start` - Начать MS OAuth
- `POST /api/v1/auth/microsoft/login/complete` - Завершить MS OAuth
- `POST /api/v1/auth/microsoft/refresh` - Обновить токен
- `GET /api/v1/auth/profile` - Текущий профиль
- `POST /api/v1/auth/logout` - Выйти

### Settings
- `GET /api/v1/settings/` - Получить настройки
- `PATCH /api/v1/settings/` - Обновить настройки
- `GET /api/v1/settings/java/` - Список Java
- `POST /api/v1/settings/java/detect` - Автодетект Java

### Servers
- `GET /api/v1/servers/` - Список серверов
- `POST /api/v1/servers/` - Добавить сервер
- `GET /api/v1/servers/{server_id}` - Получить сервер
- `PATCH /api/v1/servers/{server_id}` - Обновить сервер
- `DELETE /api/v1/servers/{server_id}` - Удалить сервер
- `GET /api/v1/servers/{server_id}/ping` - Ping сервера
- `POST /api/v1/servers/{server_id}/connect` - Подключиться

### AI Chat
- `WS /api/v1/ai/chat` - AI чат с streaming
- `POST /api/v1/ai/chat` - AI чат (REST, без streaming)

## Зависимости

- FastAPI >= 0.109.0
- Uvicorn >= 0.27.0
- Pydantic >= 2.5.0
- httpx >= 0.26.0
- aiosqlite >= 0.19.0
- minecraft-launcher-lib >= 5.0.0
- cryptography >= 42.0.0
- loguru >= 0.7.0
- aiohttp >= 3.9.0
- websockets >= 12.0
- msal >= 1.28.0
- mcstatus >= 11.1.0
- llama-cpp-python >= 0.2.0
