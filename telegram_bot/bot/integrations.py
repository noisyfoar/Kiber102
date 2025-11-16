from __future__ import annotations

from typing import Any, Dict
import httpx

from ..config import settings

class ApiGatewayClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token_by_user: dict[int, str] = {}
        self._profile_by_user: dict[int, Dict[str, Any]] = {}
        self._guest_sessions: dict[int, str] = {}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=15)

    def _format_phone(self, phone: str) -> str:
        """Форматирует номер телефона в формат +7XXXXXXXXXX"""
        if not phone:
            return ""
        cleaned = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        if cleaned.startswith("+7"):
            digits = cleaned[2:]
            if digits.isdigit() and len(digits) == 10:
                return "+7" + digits
            return cleaned
        
        if cleaned.startswith("8") and len(cleaned) == 11 and cleaned[1:].isdigit():
            return "+7" + cleaned[1:]
        
        if cleaned.startswith("7") and len(cleaned) == 11 and cleaned[1:].isdigit():
            return "+" + cleaned
        
        if cleaned.startswith("9") and len(cleaned) == 10 and cleaned.isdigit():
            return "+7" + cleaned
        
        if cleaned.startswith("+"):
            return cleaned
        
        if cleaned.isdigit():
            if len(cleaned) == 10:
                return "+7" + cleaned
            elif len(cleaned) == 11 and cleaned.startswith("7"):
                return "+" + cleaned
            elif len(cleaned) == 11 and cleaned.startswith("8"):
                return "+7" + cleaned[1:]
        
        return cleaned

    async def register(
        self,
        user_id: int,
        phone: str,
        name: str,
        birth_date: str,
    ) -> Dict[str, Any]:
        formatted_phone = self._format_phone(phone)
        if not formatted_phone or not formatted_phone.startswith("+7") or len(formatted_phone) != 12 or not formatted_phone[2:].isdigit():
            raise ValueError("Неверный формат номера телефона")
        
        if not name or not name.strip():
            raise ValueError("Имя не может быть пустым")
        
        if not birth_date:
            raise ValueError("Дата рождения обязательна")
        
        payload = {
            "phone": formatted_phone,
            "name": name.strip(),
            "birth_date": birth_date,
        }
        async with self._client() as client:
            resp = await client.post("/auth/register", json=payload)
            if resp.status_code >= 400:
                try:
                    error_data = resp.json()
                    error_text = error_data.get("detail", resp.text) if isinstance(error_data, dict) else resp.text
                except:
                    error_text = resp.text
                raise ValueError(f"Ошибка регистрации ({resp.status_code}): {error_text}")
            
            data = resp.json()
            token = data["token"]
            user_info = data.get("user", {})
            self._token_by_user[user_id] = token
            self._profile_by_user[user_id] = {
                "phone": user_info.get("phone", payload["phone"]),
                "name": user_info.get("name", name),
                "birth_date": user_info.get("birth_date", birth_date),
            }
            return {"token": token, "user": user_info}

    async def login_with_phone(
        self,
        user_id: int,
        phone: str,
    ) -> Dict[str, Any]:
        payload = {"phone": self._format_phone(phone)}
        async with self._client() as client:
            resp = await client.post("/auth/login", json=payload)
            if resp.status_code == 404:
                raise ValueError("Пользователь не найден. Пожалуйста, зарегистрируйтесь через /register")
            resp.raise_for_status()
            data = resp.json()
            token = data["token"]
            user_info = data.get("user", {})
            self._token_by_user[user_id] = token
            self._profile_by_user[user_id] = {
                "phone": user_info.get("phone", payload["phone"]),
                "name": user_info.get("name", ""),
                "birth_date": user_info.get("birth_date", ""),
            }
            return {"token": token, "user": user_info}

    def has_session(self, user_id: int) -> bool:
        return user_id in self._token_by_user

    async def ensure_login(self, user_id: int) -> str:
        if user_id not in self._token_by_user:
            raise PermissionError("Пожалуйста, авторизуйтесь командой /auth перед отправкой снов.")
        return self._token_by_user[user_id]

    def _get_guest_session_id(self, user_id: int) -> str:
        if user_id not in self._guest_sessions:
            import time
            import random
            self._guest_sessions[user_id] = f"guest_{user_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        return self._guest_sessions[user_id]

    async def send_chat(
        self,
        user_id: int,
        text: str,
        guest_profile: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if user_id in self._token_by_user:
            token = self._token_by_user[user_id]
            headers = {"Authorization": f"Bearer {token}"}
            async with self._client() as client:
                resp = await client.post("/chat", json={"message": text}, headers=headers)
                resp.raise_for_status()
                return resp.json()
        else:
            guest_session_id = self._get_guest_session_id(user_id)
            payload = {
                "message": text,
                "guest_session_id": guest_session_id,
                "guest_profile": guest_profile or {},
            }
            async with self._client() as client:
                resp = await client.post("/chat", json=payload)
                resp.raise_for_status()
                return resp.json()

    async def delete_sessions(self, user_id: int) -> None:
        token = await self.ensure_login(user_id)
        headers = {"Authorization": f"Bearer {token}"}
        async with self._client() as client:
            resp = await client.delete("/sessions", headers=headers)
            resp.raise_for_status()

    async def request_support_link(self, user_id: int, amount: float = 199.0) -> str:
        if user_id not in self._token_by_user:
            return "Для поддержки проекта необходимо авторизоваться через /auth"
        try:
            payment_data = await self.create_payment(
                user_id=user_id,
                amount=amount,
                description="Поддержка проекта ИИ Сонник"
            )
            link = payment_data.get("payment_url", "https://pay.example.com/support/kiber102")
            # Добавляем chat_url для кнопки "Вернуться в чат" на странице оплаты
            chat_url = ""
            try:
                if getattr(settings, "bot_username", ""):
                    chat_url = f"https://t.me/{settings.bot_username}"
                elif getattr(settings, "public_base_url", ""):
                    chat_url = settings.public_base_url.rstrip("/")
            except Exception:
                chat_url = ""
            if chat_url:
                separator = "&" if ("?" in link) else "?"
                link = f"{link}{separator}chat_url={httpx.QueryParams({'chat_url': chat_url})['chat_url']}"
            # Переписываем базовый URL на публичный, если задан TELEGRAM_PUBLIC_BASE_URL
            public_base = (settings.public_base_url or "").rstrip("/")
            try:
                from urllib.parse import urlparse
                parsed = urlparse(link)
                # Если есть публичная база — всегда используем её
                if public_base and parsed.scheme and parsed.netloc:
                    link = f"{public_base}{parsed.path}"
                    if parsed.query:
                        link += f"?{parsed.query}"
                # Фолбэк: если ссылка указывает на внутренний api_gateway — подменяем на localhost:8000
                elif parsed.netloc and "api_gateway" in parsed.netloc:
                    fallback_base = "http://localhost:8000"
                    link = f"{fallback_base}{parsed.path}"
                    if parsed.query:
                        link += f"?{parsed.query}"
            except Exception:
                # В крайнем случае — простая подстановка на основе известных шаблонов
                if public_base:
                    link = link.replace("http://api_gateway:8000", public_base)\
                               .replace("https://api_gateway:8000", public_base)\
                               .replace("http://api_gateway", public_base)\
                               .replace("https://api_gateway", public_base)
                else:
                    link = link.replace("http://api_gateway:8000", "http://localhost:8000")\
                               .replace("https://api_gateway:8000", "http://localhost:8000")\
                               .replace("http://api_gateway", "http://localhost:8000")\
                               .replace("https://api_gateway", "http://localhost:8000")
            return link
        except Exception as e:
            return f"Ошибка при создании платежа: {str(e)}"

    async def transcribe_audio(self, user_id: int, audio_base64: str) -> str:
        payload = {"audio_base64": audio_base64}
        async with self._client() as client:
            resp = await client.post("/asr", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", "")

    async def text_to_speech(self, text: str, lang: str = "ru", slow: bool = False) -> bytes:
        payload = {"text": text, "lang": lang, "slow": slow}
        async with self._client() as client:
            resp = await client.post("/tts", json=payload)
            resp.raise_for_status()
            data = resp.json()
            import base64
            audio_base64 = data.get("audio_base64", "")
            return base64.b64decode(audio_base64)

    async def get_user_profile(self, user_id: int) -> Dict[str, Any] | None:
        if user_id not in self._token_by_user:
            return None
        return self._profile_by_user.get(user_id)

    async def create_payment(self, user_id: int, amount: float, description: str) -> Dict[str, Any]:
        token = await self.ensure_login(user_id)
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"amount": amount, "description": description}
        async with self._client() as client:
            resp = await client.post("/payments", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def logout(self, user_id: int) -> None:
        self._token_by_user.pop(user_id, None)
        self._profile_by_user.pop(user_id, None)
        self._guest_sessions.pop(user_id, None)