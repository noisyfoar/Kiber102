from __future__ import annotations

from functools import lru_cache
from typing import Any, AsyncGenerator, Dict

import httpx
from fastapi import Depends, Header, HTTPException, status

from ..config import settings
from .auth import decode_token


@lru_cache
def get_settings():
    return settings


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(timeout=15) as client:
        yield client


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> Dict[str, Any]:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user_url = str(settings.user_service_url).rstrip("/")
    resp = await client.get(f"{user_url}/users/{user_id}")
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return resp.json()


async def get_current_user_optional(
    authorization: str | None = Header(None, alias="Authorization"),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> Dict[str, Any] | None:
    """Опциональная авторизация для гостевого режима."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user_url = str(settings.user_service_url).rstrip("/")
    resp = await client.get(f"{user_url}/users/{user_id}")
    if resp.status_code >= 400:
        return None
    return resp.json()
