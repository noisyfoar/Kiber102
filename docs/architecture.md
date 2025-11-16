# Архитектура «ИИ Сонник»

## Состав

- **API Gateway (FastAPI)** — единая точка входа, авторизация JWT, прокси к сервисам, агрегация ответов.
- **User Service (FastAPI + SQLAlchemy)** — хранение профилей и истории сессий (PostgreSQL). Предоставляет REST CRUD.
- **Chat Service (FastAPI)** — диалоги, дерево состояний, интеграция с GigaChat или fallback-интерпретатор, ASR/TTS.
- **Payment Service (FastAPI)** — mock-заглушка платёжного провайдера: генерирует ссылки и отмечает платежи без реального Робокассы API.
- **Frontend (React + Vite + Tailwind)** — веб-клиент, аутентификация, интерфейс чата, кнопка поддержки и интеграция c ASR/TTS.
- **Telegram Bot (Aiogram)** — зеркальный чат через API Gateway.
- **DB** — миграции и схема PostgreSQL, описаны в `db/schema.sql`.
- **docker-compose** — локальный запуск всех контейнеров, Postgres и Redis.

## Поток данных

1. Пользователь логинится по телефону → API Gateway → User Service (create/upsert) → JWT.
2. Сообщение уходит в API Gateway `/chat` → Chat Service, ответ сохраняется в User Service.
3. Chat Service добавляет центрированную эмпатию благодаря `dialog_tree` и хранит short-context в Redis (или in-memory fallback).
4. Web/Telegram клиенты могут использовать `/asr` и `/tts` через Gateway.
5. `/payments` инициирует ссылку mock-провайдера, callback просто отмечает платёж в памяти (без внешнего API).

## Технологические детали

- FastAPI, Pydantic v2, SQLAlchemy 2.0 (PostgreSQL), httpx, jose, redis/gTTS/SpeechRecognition.
- React 18, Tailwind 3, Vite 5.
- Aiogram 3 для бота.
- Dockerfiles для каждого сервиса, `.env` общая, docker-compose поднимает Postgres, Redis, все микросервисы и фронт.

