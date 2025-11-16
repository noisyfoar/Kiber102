## 🚀 Быстрый старт(Реализовано при помощи ИИ)

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