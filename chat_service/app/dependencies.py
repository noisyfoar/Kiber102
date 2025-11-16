from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from ..config import settings
from .dialog_tree import DialogManager
from .llm import DreamInterpreter


class SessionStateStore:
    """A lightweight conversation memory with optional Redis backend."""

    def __init__(self, redis_url: str | None, max_messages: int = 5) -> None:
        self.redis_url = redis_url
        self.max_messages = max_messages
        self._memory: dict[str, list[dict[str, str]]] = {}
        self._redis = None
        if redis_url:
            try:
                import redis  # type: ignore

                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
            except Exception:
                self._redis = None

    def _key(self, user_id: str) -> str:
        return f"dream:ctx:{user_id}"

    def read(self, user_id: str) -> List[dict[str, str]]:
        if self._redis:
            raw = self._redis.lrange(self._key(user_id), 0, self.max_messages - 1)
            return [json.loads(item) for item in raw]
        return self._memory.get(user_id, [])

    def append(self, user_id: str, message: str, response: str) -> None:
        entry = {"user": message, "bot": response}
        if self._redis:
            self._redis.lpush(self._key(user_id), json.dumps(entry, ensure_ascii=False))
            self._redis.ltrim(self._key(user_id), 0, self.max_messages - 1)
            return
        history = self._memory.setdefault(user_id, [])
        history.insert(0, entry)
        del history[self.max_messages :]

    def clear(self, user_id: str) -> None:
        if self._redis:
            self._redis.delete(self._key(user_id))
            return
        self._memory.pop(user_id, None)


@lru_cache
def get_session_store() -> SessionStateStore:
    return SessionStateStore(settings.redis_url, settings.max_context_messages)


@lru_cache
def get_interpreter() -> DreamInterpreter:
    return DreamInterpreter(settings=settings, dialog_manager=DialogManager())
