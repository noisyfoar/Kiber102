from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..config import settings
from .auth import create_access_token
from .dependencies import get_current_user, get_current_user_optional, get_http_client

router = APIRouter()

# Ранее здесь был in-memory агрегатор "снов" по стадиям (greeting → closing).
# Логика объединения по стадиям отключена по новым требованиям.


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=5)
    name: str = Field(..., min_length=1)
    birth_date: str = Field(...)


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=5)


class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]


class ChatGatewayRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    guest_session_id: str | None = Field(None, description="ID гостевой сессии (для неавторизованных пользователей)")
    guest_profile: Dict[str, Any] | None = Field(None, description="Профиль гостя (имя, дата рождения)")


class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0.0)
    description: str


class SpeechRequest(BaseModel):
    audio_base64: str


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    lang: str = Field(default="ru", description="Язык синтеза (ru, en, и др.)")
    slow: bool = Field(default=False, description="Медленная речь")

class MigrateGuestRequest(BaseModel):
    turns: list[Dict[str, str]] = Field(
        default_factory=list,
        description="Последовательность ходов [{'user': str, 'bot': str}]"
    )
    profile: Dict[str, Any] | None = Field(default=None)

@router.post("/auth/register", response_model=LoginResponse)
async def register(payload: RegisterRequest, client=Depends(get_http_client)) -> LoginResponse:
    base_url = str(settings.user_service_url).rstrip("/")
    resp = await client.post(f"{base_url}/auth/register", json=payload.dict())
    if resp.status_code >= 400:
        # Пытаемся извлечь детали ошибки из JSON
        try:
            error_data = resp.json()
            if isinstance(error_data, dict) and "detail" in error_data:
                detail = error_data["detail"]
            else:
                detail = resp.text
        except:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)
    user = resp.json()
    token = create_access_token(user["id"])
    return LoginResponse(token=token, user=user)


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest, client=Depends(get_http_client)) -> LoginResponse:
    base_url = str(settings.user_service_url).rstrip("/")
    resp = await client.post(f"{base_url}/auth/login", json=payload.dict())
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    user = resp.json()
    token = create_access_token(user["id"])
    return LoginResponse(token=token, user=user)


@router.post("/chat")
async def chat(
    payload: ChatGatewayRequest,
    client=Depends(get_http_client),
    current_user=Depends(get_current_user_optional),
):
    # Определяем, авторизован ли пользователь или это гость
    is_guest = current_user is None
    
    if is_guest:
        # Гостевой режим
        guest_session_id = payload.guest_session_id or "guest_anonymous"
        profile = payload.guest_profile or {}
        user_id = hash(guest_session_id) % (10**9)  # Генерируем числовой ID из session_id
        previous_sessions = []
        session_count = 0
    else:
        # Авторизованный пользователь
        user_id = current_user["id"]
        profile = {"name": current_user.get("name"), "birth_date": current_user.get("birth_date")}
        last_session: Dict[str, Any] | None = None
        
        # Получаем историю предыдущих сессий для персонализации
        user_url = str(settings.user_service_url).rstrip("/")
        sessions_resp = await client.get(f"{user_url}/users/{user_id}/sessions", params={"limit": 10})
        previous_sessions = []
        session_count = 0
        if sessions_resp.status_code == 200:
            sessions_data = sessions_resp.json()
            session_count = len(sessions_data)
            # Преобразуем в формат для chat_service
            previous_sessions = [
                {
                    "message": s.get("message", ""),
                    "mood": s.get("mood", "unknown"),
                    "created_at": s.get("created_at", ""),
                }
                for s in sessions_data
            ]
            if sessions_data:
                last_session = sessions_data[0]
    
    chat_url = str(settings.chat_service_url).rstrip("/")
    chat_resp = await client.post(
        f"{chat_url}/chat",
        json={
            "user_id": user_id,
            "message": payload.message,
            "profile": profile,
            "previous_sessions": previous_sessions,
            "session_count": session_count,
            "is_guest": is_guest,
        },
    )
    if chat_resp.status_code >= 400:
        raise HTTPException(status_code=chat_resp.status_code, detail=chat_resp.text)
    chat_data = chat_resp.json()
    
    # Подсказка о прошлом сне для первого сообщения новой сессии
    try:
        if not is_guest:
            context_list = chat_data.get("context") or []
            is_first_turn = len(context_list) <= 1
            # last_session доступен только для авторизованных
            if is_first_turn and 'last_session' in locals() and last_session:
                prev_summary = (last_session.get("response") or "").strip()
                prev_message = (last_session.get("message") or "").strip()
                base = prev_summary or prev_message
                if base:
                    short = base.replace("\n", " ").strip()
                    if len(short) > 160:
                        short = short[:157].rstrip() + "…"
                    prefix = f"Привет! Кстати, в прошлый раз мы обсуждали: {short}"
                    reply_text = chat_data.get("reply", "")
                    chat_data["reply"] = f"{prefix}\n\n{reply_text}" if reply_text else prefix
    except Exception:
        pass

    # Если этап завершения — получаем summary от chat_service и возвращаем его фронту/боту
    try:
        if chat_data.get("stage") == "closing":
            chat_url = str(settings.chat_service_url).rstrip("/")
            turns = chat_data.get("context") or []
            # Получаем summary финального сна
            sum_resp = await client.post(
                f"{chat_url}/summarize",
                json={
                    "turns": [{"user": t.get("user",""), "bot": t.get("bot","")} for t in turns],
                    "profile": profile or {},
                },
            )
            summary: str | None = None
            if sum_resp.status_code < 400:
                summary = sum_resp.json().get("summary")
                if summary:
                    chat_data["summary"] = summary
            # Автосохранение для авторизованных пользователей
            if not is_guest:
                # Консолидируем пользовательские сообщения
                consolidated_user = " ".join([t.get("user","") for t in turns if t.get("user")]).strip()[:2000]
                user_url = str(settings.user_service_url).rstrip("/")
                await client.post(
                    f"{user_url}/users/{user_id}/sessions",
                    json={
                        "message": consolidated_user or payload.message,
                        "response": (summary or chat_data.get("reply", ""))[:5000],
                        "mood": "closing",
                    },
                )
            # Сброс состояния диалога, чтобы начать новый сон
            try:
                await client.delete(f"{chat_url}/sessions/{user_id}")
            except Exception:
                # Не критично, если очистка не удалась
                pass
    except Exception:
        # Ошибки автосохранения/очистки не должны ломать основной ответ чата
        pass

    # Добавляем флаг, что это гостевая сессия и нужно предложить регистрацию
    if is_guest:
        chat_data["is_guest"] = True
        chat_data["suggest_registration"] = chat_data.get("stage") == "analysis"  # Предлагаем после анализа
    
    return chat_data


@router.get("/sessions")
async def sessions(
    limit: int = 20,
    client=Depends(get_http_client),
    current_user=Depends(get_current_user),
):
    user_url = str(settings.user_service_url).rstrip("/")
    resp = await client.get(
        f"{user_url}/users/{current_user['id']}/sessions", params={"limit": limit}
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.post("/payments")
async def create_payment(
    payload: PaymentRequest,
    request: Request,
    client=Depends(get_http_client),
    current_user=Depends(get_current_user),
):
    payment_url = str(settings.payment_service_url).rstrip("/")
    resp = await client.post(
        f"{payment_url}/pay",
        json={"user_id": current_user["id"], **payload.dict()},
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    invoice_id = data.get("invoice_id")
    # Строим публичную ссылку оплаты
    # 1) если задан API_PUBLIC_BASE_URL — используем его
    # 2) иначе пробуем X-Forwarded-Proto/Host (для прокси)
    # 3) иначе используем request.base_url (может быть внутренним)
    if settings.public_base_url:
        base_url = settings.public_base_url.rstrip("/")
    else:
        forwarded_proto = request.headers.get("x-forwarded-proto")
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            scheme = forwarded_proto or request.url.scheme
            base_url = f"{scheme}://{forwarded_host}".rstrip("/")
        else:
            base_url = str(request.base_url).rstrip("/")
    public_payment_url = f"{base_url}/payments/{invoice_id}"
    return {"invoice_id": invoice_id, "payment_url": public_payment_url}


@router.get("/payments/{invoice_id}")
async def payment_page(
    invoice_id: str,
    request: Request,
    client=Depends(get_http_client),
):
    """Прокси для страницы оплаты"""
    from fastapi.responses import HTMLResponse
    
    payment_url = str(settings.payment_service_url).rstrip("/")
    # Передаем query параметры из запроса
    params = dict(request.query_params)
    query_string = "&".join([f"{k}={v}" for k, v in params.items()]) if params else ""
    url = f"{payment_url}/payments/{invoice_id}" + (f"?{query_string}" if query_string else "")
    
    resp = await client.get(url)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    
    return HTMLResponse(content=resp.text)


@router.post("/payments/{invoice_id}/confirm")
async def confirm_payment(
    invoice_id: str,
    payload: dict,
    client=Depends(get_http_client),
):
    """Прокси для подтверждения платежа"""
    payment_url = str(settings.payment_service_url).rstrip("/")
    resp = await client.post(
        f"{payment_url}/payments/{invoice_id}/confirm",
        json=payload,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.post("/sessions/migrate")
async def migrate_guest_session(
    payload: MigrateGuestRequest,
    client=Depends(get_http_client),
    current_user=Depends(get_current_user),
):
    """
    Импортирует гостевой диалог в аккаунт пользователя как одну завершенную сессию.
    """
    turns = payload.turns or []
    profile = payload.profile or {}
    if not turns:
        return {"status": "skipped", "reason": "empty_turns"}
    # Получаем summary у chat_service (как в /chat при closing)
    chat_url = str(settings.chat_service_url).rstrip("/")
    try:
        sum_resp = await client.post(
            f"{chat_url}/summarize",
            json={
                "turns": [{"user": t.get("user",""), "bot": t.get("bot","")} for t in turns],
                "profile": profile,
            },
        )
        if sum_resp.status_code >= 400:
            summary = " ".join([t.get("user","") for t in turns if t.get("user")]).strip()[:1000]
        else:
            summary = sum_resp.json().get("summary") or " ".join([t.get("user","") for t in turns if t.get("user")]).strip()[:1000]
    except Exception:
        summary = " ".join([t.get("user","") for t in turns if t.get("user")]).strip()[:1000]

    # Консолидируем текст пользователя
    consolidated_user = " ".join([t.get("user","") for t in turns if t.get("user")]).strip()[:2000]

    # Сохраняем у user_service
    user_url = str(settings.user_service_url).rstrip("/")
    save_resp = await client.post(
        f"{user_url}/users/{current_user['id']}/sessions",
        json={
            "message": consolidated_user or (turns[-1].get("user","") if turns else ""),
            "response": summary or (turns[-1].get("bot","") if turns else ""),
            "mood": "closing",
        },
    )
    if save_resp.status_code >= 400:
        raise HTTPException(status_code=save_resp.status_code, detail=save_resp.text)
    return {"status": "ok"}

@router.post("/asr")
async def speech_to_text(payload: SpeechRequest, client=Depends(get_http_client)):
    chat_url = str(settings.chat_service_url).rstrip("/")
    resp = await client.post(f"{chat_url}/asr", json=payload.dict())
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.post("/tts")
async def text_to_speech(payload: TtsRequest, client=Depends(get_http_client)):
    chat_url = str(settings.chat_service_url).rstrip("/")
    resp = await client.post(f"{chat_url}/tts", json=payload.dict())
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sessions(
    client=Depends(get_http_client),
    current_user=Depends(get_current_user),
):
    user_url = str(settings.user_service_url).rstrip("/")
    resp = await client.delete(f"{user_url}/users/{current_user['id']}/sessions")
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    chat_url = str(settings.chat_service_url).rstrip("/")
    chat_resp = await client.delete(f"{chat_url}/sessions/{current_user['id']}")
    if chat_resp.status_code >= 400:
        raise HTTPException(status_code=chat_resp.status_code, detail=chat_resp.text)