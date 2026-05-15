# NexoraLauncher Frontend

Frontend GUI приложение на PyQt6.

## Установка

```bash
pip install -r frontend-requirements.txt
```

## Запуск

```bash
cd frontend
python main.py
```

## Структура

```
frontend/
├── main.py                  # Точка входа
├── app.py                   # Главное окно
├── pages/                   # Страницы приложения
│   ├── home_page.py
│   ├── instances_page.py
│   ├── versions_page.py
│   ├── mods_page.py
│   ├── modpacks_page.py
│   ├── maps_page.py
│   ├── resourcepacks_page.py
│   ├── shaders_page.py
│   ├── servers_page.py
│   ├── ai_chat_page.py
│   └── settings_page.py
├── services/                # API клиенты
│   ├── api_client.py
│   ├── instances_api.py
│   └── ...
└── models/                  # DTO модели
```

## Архитектура

Frontend построен по принципу толстого клиента:
- Все данные получаются через HTTP API от backend
- UI полностью отделён от бизнес-логики
- Async API клиенты для неблокирующих запросов

## Зависимости

- PyQt6 >= 6.6.0
- aiohttp >= 3.9.0
- requests >= 2.31.0
- loguru >= 0.7.0
- websocket-client >= 1.6.0
