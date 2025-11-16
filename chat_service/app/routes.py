from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .asr_tts import synthesize_speech, transcribe_audio
from .dependencies import get_interpreter, get_session_store

router = APIRouter()


class UserProfile(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    message: str = Field(..., min_length=1, max_length=2000)
    profile: UserProfile = Field(default_factory=UserProfile)
    previous_sessions: List[dict] = Field(default_factory=list, description="История предыдущих сессий")
    session_count: int = Field(default=0, description="Количество предыдущих сессий")
    is_guest: bool = Field(default=False, description="Является ли пользователь гостем")


class ChatResponse(BaseModel):
    reply: str
    stage: str
    hint: str  # Подсказка для пользователя
    context: List[dict[str, str]]


class SummarizeRequest(BaseModel):
    turns: List[dict[str, str]] = Field(..., description="Список ходов {'user': str, 'bot': str} в хронологическом порядке")
    profile: Optional[UserProfile] = None


class SummarizeResponse(BaseModel):
    summary: str


class AsrRequest(BaseModel):
    audio_base64: str


class AsrResponse(BaseModel):
    text: str


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    lang: str = Field(default="ru", description="Язык синтеза (ru, en, и др.)")
    slow: bool = Field(default=False, description="Медленная речь")


class TtsResponse(BaseModel):
    audio_base64: str
    format: str = Field(default="mp3", description="Формат аудио")


@router.post("/chat", response_model=ChatResponse)
def handle_chat(
    payload: ChatRequest,
    interpreter=Depends(get_interpreter),
    store=Depends(get_session_store),
) -> ChatResponse:
    user_id = str(payload.user_id)
    history = store.read(user_id)
    
    # Получаем hint для текущего этапа
    from .dialog_tree import DialogManager
    dialog_manager = DialogManager()
    step = dialog_manager.next_step(history, payload.message)
    
    reply, stage = interpreter.interpret(
        payload.profile.dict(),
        payload.message,
        history,
        previous_sessions=payload.previous_sessions,
        session_count=payload.session_count,
    )
    store.append(user_id, payload.message, reply)
    
    return ChatResponse(
        reply=reply,
        stage=stage,
        hint=step.hint,
        context=store.read(user_id)
    )


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_dream(
    payload: SummarizeRequest,
    interpreter=Depends(get_interpreter),
) -> SummarizeResponse:
    profile_dict = payload.profile.dict() if payload.profile else {}
    summary = interpreter.summarize_dream(payload.turns, profile_dict)
    return SummarizeResponse(summary=summary)


@router.post("/asr", response_model=AsrResponse)
def handle_asr(payload: AsrRequest) -> AsrResponse:
    return AsrResponse(text=transcribe_audio(payload.audio_base64))


@router.post("/tts", response_model=TtsResponse)
def handle_tts(payload: TtsRequest) -> TtsResponse:
    """Синтезирует речь из текста."""
    audio_base64 = synthesize_speech(payload.text, lang=payload.lang, slow=payload.slow)
    return TtsResponse(audio_base64=audio_base64, format="mp3")


@router.delete("/sessions/{user_id}", status_code=204)
def clear_session_history(
    user_id: int,
    store=Depends(get_session_store),
) -> None:
    store.clear(str(user_id))
