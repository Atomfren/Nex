# Быстрый старт NexoraLauncher

## Предварительные требования

- Python 3.11+
- pip
- (Опционально) virtualenv

## 1. Установка зависимостей

```bash
# Установка всех зависимостей
pip install -r requirements.txt
```

## 2. Запуск приложения

### Вариант A: Единый запуск (рекомендуется)

```bash
python -m frontend.main
```

Эта команда автоматически:
1. Запустит backend сервер на порту 8000
2. Подождёт пока backend подготовится
3. Запустит frontend GUI

### Вариант B: Раздельный запуск

```bash
# Терминал 1 - Backend
cd ARCHITECTURE/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Терминал 2 - Frontend
cd ARCHITECTURE/frontend
python main.py
```

### Вариант C: Только frontend (если backend уже запущен)

```bash
cd ARCHITECTURE/frontend
python main.py
```

## 3. Проверка работы

### Backend

Откройте браузер и перейдите по адресу:
- http://127.0.0.1:8000/docs - Swagger UI документация
- http://127.0.0.1:8000/api/v1/health - Health check

### Frontend

Приложение должно открыться с главным окном и боковой панелью навигации.

## 4. Структура проекта

```
ARCHITECTURE/
├── backend/                    # Backend сервис
│   ├── main.py                # FastAPI приложение
│   ├── config.py              # Конфигурация
│   ├── api/v1/                # API endpoints
│   │   ├── health.py
│   │   ├── instances.py
│   │   ├── minecraft.py
│   │   ├── mods.py
│   │   ├── auth.py
│   │   ├── ai.py              # WebSocket
│   │   └── settings.py
│   ├── core/                  # Бизнес-логика
│   ├── services/              # Внешние API
│   ├── db/                    # Database
│   └── models/                # DTO модели
│
├── frontend/                   # Frontend GUI (PyQt6)
│   ├── main.py                # Точка входа
│   ├── app.py                 # Главное окно
│   ├── pages/                 # Страницы
│   │   ├── home_page.py
│   │   ├── instances_page.py
│   │   ├── versions_page.py
│   │   ├── mods_page.py
│   │   ├── modpacks_page.py
│   │   ├── maps_page.py
│   │   ├── resourcepacks_page.py
│   │   ├── shaders_page.py
│   │   ├── servers_page.py
│   │   ├── ai_chat_page.py
│   │   └── settings_page.py
│   ├── services/              # API клиенты
│   │   ├── api_client.py
│   │   └── instances_api.py
│   └── models/                # DTO модели
│
├── shared/                     # Общие модули
│   ├── config.py
│   ├── crypto.py
│   ├── i18n.py
│   └── paths.py
│
├── backend-requirements.txt
├── frontend-requirements.txt
├── requirements.txt
├── README.md
├── TECHNICAL_SPEC.md
└── QUICKSTART.md
```

## 5. Разработка

### Backend

```bash
cd backend
uvicorn main:app --reload
```

Изменения в коде автоматически перезагрузят сервер.

### Frontend

```bash
cd frontend
python main.py
```

Перезапустите для применения изменений.

## 6. Тестирование

```bash
# Unit тесты backend
pytest backend/tests/

# Интеграционные тесты
pytest tests/integration/
```

## 7. AI Помощник

Для работы AI чата требуется GGUF модель:

1. Скачайте модель (например, Llama 2 7B Q4_K_M.gguf)
2. Поместите в `ARCHITECTURE/data/` или укажите путь:
```bash
# Windows
set QUANTUMLAUNCHER_BACKEND_AI_MODEL_PATH=C:\models\model.gguf

# Linux/Mac
export QUANTUMLAUNCHER_BACKEND_AI_MODEL_PATH=/home/user/models/model.gguf
```

## 8. Известные проблемы

### Backend не запускается

Проверьте, что порт 8000 свободен:
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### API не отвечает

Убедитесь, что backend запущен:
```bash
curl http://127.0.0.1:8000/api/v1/health
```
