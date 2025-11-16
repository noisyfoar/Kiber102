from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt

from ..config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.access_token_exp_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:  # pragma: no cover - falls back to FastAPI error handler
        raise ValueError("Invalid or expired token") from exc
