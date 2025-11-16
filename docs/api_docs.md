# API Gateway (FastAPI)

## POST `/auth/login`
- body: `{ "phone": "+7999...", "name": "...", "birth_date": "YYYY-MM-DD" }`
- response: `{ "token": "...", "user": { ... } }`

## POST `/chat`
- headers: `Authorization: Bearer <token>`
- body: `{ "message": "..." }`
- response: `{ "reply": "...", "stage": "analysis", "context": [...] }`

## GET `/sessions`
- headers: `Authorization`
- query: `limit`
- response: `[{ "message": "...", "response": "...", "mood": "analysis" }, ...]`

## POST `/payments`
- headers: `Authorization`
- body: `{ "amount": 199.0, "description": "Поддержка" }`
- response: `{ "payment_url": "...", "invoice_id": "..." }`

## POST `/asr`
- body: `{ "audio_base64": "..." }`
- response: `{ "text": "..." }`

## POST `/tts`
- body: `{ "text": "..." }`
- response: `{ "audio_base64": "..." }`

---

# User Service
- `POST /auth/login` — создать/обновить пользователя.
- `GET /users`, `GET /users/{id}` — список, карточка.
- `GET /users/{id}/sessions` — история.
- `POST /users/{id}/sessions` — сохранить ответ чат-бота.

---

# Chat Service
- `POST /chat` — принимает `user_id`, `message`, `profile`.
- `POST /asr` / `POST /tts`.

---

# Payment Service
- `POST /pay` — создать ссылку mock-провайдера (возвращает `payment_url`, `invoice_id`).
- `POST /callback` — принять `invoice_id` и пометить платёж оплаченным (без реального внешнего API).

