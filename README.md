project-root/  # Корневая директория проекта: содержит общие конфигурации и скрипты.
├── api_gateway/  # Микросервис: API Gateway (FastAPI) — единая точка входа, роутинг, аутентификация.
│   ├── app/  # Основная логика приложения.
│   │   ├── __init__.py  # Инициализация пакета.
│   │   ├── main.py  # Точка входа: запуск FastAPI приложения, настройка роутеров и WebSockets.
│   │   ├── routes.py  # Определение эндпоинтов: роутинг к другим сервисам (например, /auth -> User Service).
│   │   ├── auth.py  # Логика аутентификации: JWT-токены, валидация запросов.
│   │   └── dependencies.py  # Зависимости: инъекция (например, для rate-limiting).
│   ├── config/  # Конфигурационные файлы.
│   │   └── settings.py  # Настройки: переменные окружения (DATABASE_URL, JWT_SECRET и т.д.).
│   ├── tests/  # Тесты для сервиса.
│   │   └── test_routes.py  # Unit- и интеграционные тесты (Pytest).
│   ├── requirements.txt  # Зависимости: fastapi, uvicorn, pydantic и т.д.
│   └── Dockerfile  # Docker-файл для контейнеризации сервиса.
├── user_service/  # Микросервис: User Service (FastAPI) — управление пользователями, авторизация, контекст.
│   ├── app/  # Основная логика.
│   │   ├── __init__.py
│   │   ├── main.py  # Запуск приложения, настройка роутеров.
│   │   ├── routes.py  # Эндпоинты: /users (CRUD), /auth (авторизация по телефону).
│   │   ├── models.py  # Pydantic-модели для валидации данных (User, Session).
│   │   ├── crud.py  # Операции с БД: create/read/update/delete для пользователей и сессий.
│   │   └── db.py  # Подключение к PostgreSQL via SQLAlchemy.
│   ├── config/  # Конфигурации.
│   │   └── settings.py  # Настройки: DATABASE_URL и т.д.
│   ├── tests/  # Тесты.
│   │   └── test_crud.py  # Тесты для операций с БД.
│   ├── requirements.txt  # Зависимости: fastapi, sqlalchemy, psycopg2.
│   └── Dockerfile  # Контейнеризация.
├── chat_service/  # Микросервис: Chat Service (FastAPI) — обработка диалогов, интеграция с GigaChat, ASR/TTS.
│   ├── app/  # Основная логика.
│   │   ├── __init__.py
│   │   ├── main.py  # Запуск, настройка роутеров и WebSockets для чата.
│   │   ├── routes.py  # Эндпоинты: /chat (обработка сообщений), /asr (распознавание речи), /tts (синтез речи).
│   │   ├── llm.py  # Интеграция с GigaChat: формирование промптов, вызов API.
│   │   ├── dialog_tree.py  # Логика дерева диалогов: state machine для эмпатичного флоу.
│   │   ├── asr_tts.py  # Функции для ASR (speech_recognition) и TTS (gtts).
│   │   └── dependencies.py  # Зависимости: для Redis (состояния сессий).
│   ├── config/  # Конфигурации.
│   │   └── settings.py  # Ключи API (GigaChat), REDIS_URL.
│   ├── tests/  # Тесты.
│   │   └── test_llm.py  # Тесты для промптов и диалогов.
│   ├── requirements.txt  # Зависимости: fastapi, gigachat-api, speech_recognition, gtts, redis.
│   └── Dockerfile  # Контейнеризация.
├── payment_service/  # Микросервис: Payment Service (FastAPI) — mock-заглушка платежей (без реальной Робокассы).
│   ├── app/  # Основная логика.
│   │   ├── __init__.py
│   │   ├── main.py  # Запуск, роутеры.
│   │   ├── routes.py  # Эндпоинты: /pay (инициация фейкового платежа), /callback (подтверждение invoice).
│   │   └── integration.py  # Логика mock-провайдера: UUID-инвойсы, in-memory состояния.
│   ├── config/  # Конфигурации.
│   │   └── settings.py  # Настройка mock-ссылок.
│   ├── tests/  # Тесты.
│   │   └── test_integration.py  # Mock-тесты для платежей.
│   ├── requirements.txt  # Зависимости: fastapi, requests (для API).
│   └── Dockerfile  # Контейнеризация.
├── frontend/  # Фронтенд: React-приложение для веб-страницы.
│   ├── src/  # Исходный код.
│   │   ├── components/  # Компоненты: ChatWindow.jsx (окно чата), AuthForm.jsx (форма авторизации).
│   │   ├── pages/  # Страницы: Home.jsx (основная страница с чатом).
│   │   ├── services/  # API-клиенты: api.js (Axios для вызовов API Gateway).
│   │   ├── App.jsx  # Корневой компонент.
│   │   └── index.jsx  # Точка входа.
│   ├── public/  # Статические файлы: index.html, иконки (луна, звезды для тематики).
│   ├── tailwind.config.js  # Конфигурация Tailwind CSS для стилей.
│   ├── package.json  # Зависимости: react, axios, socket.io-client.
│   └── Dockerfile  # Контейнеризация (для Nginx или build).
├── telegram_bot/  # Telegram-бот: Aiogram для зеркальной логики.
│   ├── bot/  # Основная логика.
│   │   ├── __init__.py
│   │   ├── main.py  # Запуск бота, диспетчер.
│   │   ├── handlers.py  # Обработчики: /start, сообщения, голос (ASR).
│   │   └── integrations.py  # Вызовы API Gateway для чата и контекста.
│   ├── config/  # Конфигурации.
│   │   └── settings.py  # BOT_TOKEN, API_GATEWAY_URL.
│   ├── requirements.txt  # Зависимости: aiogram, requests.
│   └── Dockerfile  # Контейнеризация.
├── db/  # База данных: скрипты для PostgreSQL.
│   ├── migrations/  # Миграции (Alembic): версии для схем (users, sessions, payments).
│   ├── schema.sql  # Начальная схема БД (таблицы, индексы).
│   └── alembic.ini  # Конфигурация Alembic.
├── docs/  # Документация: описания, диаграммы.
│   ├── architecture.md  # Описание архитектуры.
│   └── api_docs.md  # Swagger/OpenAPI для эндпоинтов.
├── .env  # Переменные окружения: общие (DATABASE_URL, API_KEYS).
├── docker-compose.yml  # Оркестрация: запуск всех сервисов, PostgreSQL, Redis, RabbitMQ.
├── README.md  # Общий обзор: инструкции по запуску, установке.
└── requirements.txt  # Общие зависимости (если нужно для скриптов).

## 🚀 Быстрый старт

```bash
docker compose up --build
```

Сервисы:
- API Gateway — http://localhost:8000/docs
- Frontend — http://localhost:4173
- User Service — http://localhost:8001/docs
- Chat Service — http://localhost:8002/docs
- Payment Service (mock) — http://localhost:8003/docs

## 🗄️ База данных

User Service по умолчанию подключается к PostgreSQL (см. `USER_DATABASE_URL`). В docker-compose поднимается `postgres:15` с БД `dream`. При локальном запуске без Docker также используйте PostgreSQL (SQLite больше не поддерживается).

### Локальный запуск без Docker

1. Создайте виртуальное окружение, установите зависимости конкретного сервиса (`pip install -r service/requirements.txt`).
2. Запустите uvicorn, например:
   ```bash
   uvicorn api_gateway.app.main:app --reload --port 8000
   ```
3. Для фронтенда:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🧪 Тестирование

В каждом сервисе есть директория `tests/`. Пример запуска:

```bash
cd api_gateway
pytest
```

## 🔧 Настройки

Создайте `.env` (пример ниже) и укажите ключи/URL:

```
API_JWT_SECRET=local-secret
USER_DATABASE_URL=postgresql+psycopg2://dream:dream@postgres:5432/dream
CHAT_REDIS_URL=redis://redis:6379/0
GIGACHAT_KEY=your_gigachat_api_key_here
GIGACHAT_AUTH_ENDPOINT=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
GIGACHAT_SCOPE=GIGACHAT_API_PERS
BOT_TOKEN=your_telegram_bot_token
API_GATEWAY_URL=http://localhost:8000
MOCK_PAYMENT_URL=https://mock-payments.local/pay
```

### Настройка GigaChat

Для работы с GigaChat API необходимо:
1. Получить API ключ на [developers.sber.ru](https://developers.sber.ru/products/gigachat-api)
2. Указать `GIGACHAT_KEY` в `.env`
3. При необходимости изменить `GIGACHAT_AUTH_ENDPOINT` и `GIGACHAT_SCOPE`

**Примечание**: Если авторизация через OAuth не работает, проверьте:
- Правильность формата API ключа
- Доступность эндпоинта авторизации
- Требования к заголовкам (RqUID и др.)
- Официальную документацию GigaChat API

Если проблемы сохраняются, рассмотрите использование официального Python SDK GigaChat.

## 📚 Документация

- `docs/architecture.md` — описание компонентов и потоков данных.
- `docs/api_docs.md` — краткая спецификация REST.
- `db/schema.sql` — SQL-схема для PostgreSQL.

## 💳 Mock-платежи

`payment_service` не обращается к реальной Робокассе: `/pay` создаёт UUID-инвойс и ссылку вида `<MOCK_PAYMENT_URL>/<invoice_id>`, а `/callback` достаточно вызвать с этим `invoice_id`, чтобы отметить статус `paid`.