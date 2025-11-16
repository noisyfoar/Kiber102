from __future__ import annotations

import logging
import random
import time
import uuid
import urllib3
import re
from datetime import datetime
from textwrap import dedent
from typing import List, Optional

import httpx

from ..config import settings as chat_settings
from .dialog_tree import DialogManager, DialogStep
from .dialog_chain import ImprovedDialogManager

# Подавляем предупреждения о небезопасном SSL (только для разработки)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Примечание: Если текущая реализация OAuth не работает, рассмотрите возможность
# использования официального Python SDK GigaChat (если доступен):
# pip install gigachat-python
# from gigachat import GigaChat
# 
# Альтернативно, проверьте официальную документацию:
# https://developers.sber.ru/products/gigachat-api


class OAuthTokenManager:
    """Управляет OAuth токенами для GigaChat с кэшированием."""

    def __init__(self, settings=chat_settings) -> None:
        self.settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def get_token(self) -> str | None:
        """Получает валидный OAuth токен (кэширует и обновляет при необходимости)."""
        # Если токен еще валиден, возвращаем его
        if self._token and time.time() < self._token_expires_at:
            return self._token

        # Получаем новый токен
        return self._refresh_token()

    def _refresh_token(self) -> str | None:
        """Обновляет OAuth токен через API GigaChat.
        
        Согласно официальной документации GigaChat:
        - В заголовке Authorization нужно передать 'Basic <Authorization key>'
        - Где <Authorization key> - это сам API ключ, а не base64(username:password)
        - Требуется заголовок RqUID с уникальным UUID
        - Тело запроса: scope=GIGACHAT_API_PERS (form-urlencoded)
        """
        if not self.settings.gigachat_key:
            logger.warning("GigaChat key not provided for OAuth")
            return None

        try:
            logger.info(f"Requesting OAuth token from {self.settings.gigachat_auth_endpoint}")
            
            # Генерируем уникальный RqUID для запроса
            rquid = str(uuid.uuid4())
            
            # Заголовки согласно официальной документации
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": rquid,
                # Важно: передаем ключ напрямую с префиксом "Basic ", а не используем httpx.BasicAuth
                "Authorization": f"Basic {self.settings.gigachat_key}",
            }
            
            # Тело запроса: scope в формате form-urlencoded
            data = {
                "scope": self.settings.gigachat_scope,
            }
            
            response = httpx.post(
                self.settings.gigachat_auth_endpoint,
                headers=headers,
                data=data,
                timeout=10,
                verify=False,  # Временно отключаем проверку SSL для разработки
            )
            
            # Логируем детали ошибки для отладки
            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "No response body"
                logger.error(
                    f"OAuth request failed with status {response.status_code}. "
                    f"Response: {error_text}. "
                    f"Headers: {dict(response.headers)}"
                )
            
            response.raise_for_status()
            data = response.json()
            
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 1800)  # По умолчанию 30 минут
            
            if access_token:
                self._token = access_token
                # Сохраняем время истечения с запасом в 60 секунд
                self._token_expires_at = time.time() + expires_in - 60
                logger.info(f"OAuth token obtained successfully, expires in {expires_in}s")
                return access_token
            else:
                logger.error(f"Unexpected OAuth response format: {data}")
                return None
        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"OAuth request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting OAuth token: {e}", exc_info=True)
            return None


class DreamInterpreter:
    """Wrapper that builds empathetic prompts and talks to GigaChat (optional)."""

    def __init__(self, settings=chat_settings, dialog_manager: DialogManager | None = None, use_improved: bool = True) -> None:
        self.settings = settings
        # Используем улучшенный менеджер диалогов по умолчанию
        if use_improved:
            try:
                self.dialog_manager = ImprovedDialogManager()
                self.use_improved = True
                logger.info("Using improved dialog manager with structured prompts")
            except Exception as e:
                logger.warning(f"Failed to initialize improved dialog manager: {e}, falling back to basic")
                self.dialog_manager = dialog_manager or DialogManager()
                self.use_improved = False
        else:
            self.dialog_manager = dialog_manager or DialogManager()
            self.use_improved = False
        self.oauth_manager = OAuthTokenManager(settings)

    def _calculate_age(self, birth_date: str | None) -> int | None:
        """Вычисляет возраст на основе даты рождения."""
        if not birth_date:
            return None
        try:
            birth = datetime.strptime(birth_date, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return age
        except (ValueError, TypeError):
            return None

    def _detect_emotion(self, message: str) -> str:
        """Определяет эмоциональный тон сообщения."""
        positive_words = ['хорошо', 'радость', 'счастье', 'спокойно', 'приятно', 'отлично']
        negative_words = ['страх', 'тревога', 'грустно', 'боюсь', 'плохо', 'страшно', 'ужас', 'паника']
        
        msg_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in msg_lower)
        negative_count = sum(1 for word in negative_words if word in msg_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        return "neutral"

    def build_prompt(
        self,
        user_profile: dict[str, str | None],
        message: str,
        history: List[dict[str, str]],
        previous_sessions: List[dict] | None = None,
        session_count: int = 0,
    ) -> tuple[str, DialogStep]:
        # Вычисляем возраст для персонализированного приветствия
        age = self._calculate_age(user_profile.get('birth_date'))
        age_context = ""
        if age is not None:
            age_context = f" Возраст пользователя: {age} лет. Учитывай возрастной контекст для более точного анализа."
        
        # Используем улучшенный метод построения промпта, если доступен
        if self.use_improved and hasattr(self.dialog_manager, 'build_structured_prompt'):
            emotion = self._detect_emotion(message)
            step = self.dialog_manager.next_step(history, message)
            # Проверяем, связан ли вопрос со снами
            is_dream_related = True
            if hasattr(self.dialog_manager, 'is_dream_related'):
                is_dream_related = self.dialog_manager.is_dream_related(message, history)
            prompt = self.dialog_manager.build_structured_prompt(
                step, user_profile, message, history, emotion, previous_sessions, age=age, is_dream_related=is_dream_related
            )
            return prompt, step
        
        # Fallback к старому методу
        step = self.dialog_manager.next_step(history, message)
        
        # Определяем эмоциональный тон
        emotion = self._detect_emotion(message)
        
        # Проверяем, связан ли вопрос со снами
        is_dream_related = True
        if hasattr(self.dialog_manager, 'is_dream_related'):
            is_dream_related = self.dialog_manager.is_dream_related(message, history)
        
        # Контекст пользователя
        name = user_profile.get('name') or 'друг'
        birth_date = user_profile.get('birth_date')
        age = self._calculate_age(birth_date)
        age_text = f"{age} лет" if age is not None else "не указан"
        context_lines = [
            f"Имя: {name}",
            f"Дата рождения: {birth_date or 'не указана'}",
            f"Возраст: {age_text}",
        ]
        
        # Контекст для возвращающихся пользователей
        greeting_context = ""
        if session_count == 0:
            greeting_context = "Это первая сессия пользователя. Поприветствуй тепло и создай доверительную атмосферу."
        elif session_count == 1:
            greeting_context = "Пользователь вернулся во второй раз. Спроси, как дела, есть ли новые сны или вопросы."
        elif session_count > 1:
            greeting_context = f"Пользователь уже был здесь {session_count} раз. Вспомни предыдущие разговоры и покажи, что ты помнишь о нем."
        
        # История предыдущих сессий
        previous_context = ""
        if previous_sessions and len(previous_sessions) > 0:
            previous_context = "\n\nПредыдущие сны пользователя (для выявления паттернов):\n"
            for idx, session in enumerate(previous_sessions[-3:], 1):  # Последние 3 сессии
                session_msg = session.get('message', '')[:100]
                session_mood = session.get('mood', 'unknown')
                previous_context += f"{idx}. {session_msg}... (этап: {session_mood})\n"
        
        # История текущего диалога
        history_text = ""
        if history:
            history_text = "\n".join(
                f"Пользователь: {item['user']}\nСонник: {item['bot']}" for item in reversed(history[-5:])
            )
        else:
            history_text = "История пуста (начало разговора)"
        
        # Эмоциональный контекст
        emotion_context = ""
        if emotion == "negative":
            emotion_context = "\n⚠️ ВАЖНО: Пользователь испытывает тревогу или негативные эмоции. Будь особенно поддерживающим, мягким и эмпатичным. Не усугубляй тревогу."
        elif emotion == "positive":
            emotion_context = "\n✅ Пользователь в позитивном настроении. Поддержи это состояние."
        
        # Персонализированное приветствие с учетом возраста
        personalized_greeting = ""
        if step.key == "greeting" and name and name != "друг" and age is not None and is_dream_related:
            personalized_greeting = (
                f"\nВАЖНО: Это первое сообщение пользователя. "
                f"Поприветствуй его по имени: 'Привет, {name}!'. "
                f"Упомяни его возраст ({age} лет) естественным образом, например: "
                f"'Учитывая твой возраст ({age} лет), я учту контекст для более точного анализа'. "
                f"Будь теплым и дружелюбным."
            )
        
        # Инструкция для off-topic вопросов
        off_topic_guidance = ""
        if not is_dream_related:
            off_topic_guidance = """
⚠️ ВАЖНО: Сообщение пользователя НЕ связано со снами или интерпретацией снов.
Это может быть общий вопрос, вопрос о чем-то другом, или просто разговор.

ТВОЯ ЗАДАЧА:
1. ВЕЖЛИВО объясни, что ты специализируешься на интерпретации снов
2. НЕ пытайся связать это сообщение со снами
3. НЕ давай интерпретацию или анализ этого сообщения как сна
4. Предложи вернуться к обсуждению снов
5. Будь дружелюбным и понимающим

Пример хорошего ответа:
"Извини, но я специализируюсь на интерпретации снов. Я могу помочь тебе разобраться в значении твоих снов, но не могу ответить на вопросы о [тема вопроса]. 

Расскажи, может быть, у тебя есть сон, который тебя беспокоит или интересует? Я буду рад помочь с его интерпретацией."

НЕ говори что-то вроде "это может быть связано со сном" или "возможно, это отражает твой сон".
"""
        
        # Строим улучшенный промпт
        prompt = dedent(
            f"""
            Ты "ИИ Сонник" — эмпатичный психологический ассистент для интерпретации снов.
            
            {off_topic_guidance}
            
            ТВОЯ ЗАДАЧА:
            1. Выслушать пользователя с вниманием и пониманием
            2. Задавать открытые вопросы для прояснения деталей (если нужно)
            3. Давать психологическую интерпретацию БЕЗ эзотерики и мистики
            4. Предлагать практические шаги для рефлексии и самоподдержки
            5. Поддерживать и вдохновлять пользователя
            
            СТИЛЬ ОБЩЕНИЯ:
            - Теплый, поддерживающий, как живой человек, который действительно заботится
            - Используй имя пользователя ({name}) естественно, не слишком часто
            - Избегай клише, шаблонных фраз и формальностей
            - Будь конкретным, но не директивным
            - Говори на "ты", дружелюбно
            - Используй простой, понятный язык
            
            {greeting_context}
            {personalized_greeting}
            
            ЭТАП ДИАЛОГА: {step.key}
            {step.system_prompt}
            {step.follow_up}
            
            {emotion_context}
            
            ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:
            {'; '.join(context_lines)}
            {f'Учитывай возрастной контекст ({age} лет) при интерпретации.' if age is not None else ''}
            
            {previous_context}
            
            ИСТОРИЯ ТЕКУЩЕГО ДИАЛОГА:
            {history_text}
            
            НОВОЕ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {message}
            
            ОТВЕТЬ:
            - Естественно, как живой человек
            - Кратко (2-4 абзаца), но содержательно
            - Учитывай эмоциональное состояние пользователя
            - Если это первый разговор - будь особенно теплым
            - Если пользователь возвращается - покажи, что помнишь о нем
            - Предложи конкретные шаги для рефлексии (если уместно)
            """
        ).strip()
        return prompt, step

    def _call_gigachat(self, prompt: str) -> Optional[str]:
        if not self.settings.gigachat_key:
            logger.info("GigaChat key not provided, using fallback")
            return None
        
        # Получаем OAuth токен
        oauth_token = self.oauth_manager.get_token()
        if not oauth_token:
            logger.warning("Failed to obtain OAuth token, using fallback")
            return None
        
        headers = {
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "system", "content": "Russian empathetic dream coach."}, {"role": "user", "content": prompt}],
            "temperature": self.settings.empathy_temperature,
        }
        try:
            logger.info(f"Calling GigaChat at {self.settings.gigachat_endpoint}")
            # ВНИМАНИЕ: verify=False отключает проверку SSL (небезопасно для продакшена)
            # Для продакшена нужно установить правильные CA сертификаты в контейнер
            response = httpx.post(
                self.settings.gigachat_endpoint,
                json=payload,
                headers=headers,
                timeout=15,
                verify=False,  # Отключаем проверку SSL для разработки
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if content:
                logger.info("GigaChat response received successfully")
                return content
            else:
                logger.warning(f"Unexpected GigaChat response format: {data}")
                return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning(
                    "GigaChat authentication failed (401). "
                    "GigaChat requires OAuth token. "
                    "To use GigaChat, you need to obtain an OAuth token first. "
                    "Using fallback response instead."
                )
            else:
                logger.error(f"GigaChat HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"GigaChat request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling GigaChat: {e}", exc_info=True)
            return None

    def fallback_response(
        self,
        step: DialogStep,
        message: str,
        user_profile: dict[str, str | None],
        history: List[dict[str, str]],
    ) -> str:
        name = user_profile.get("name") or "друг"
        age = self._calculate_age(user_profile.get("birth_date"))
        
        # Проверяем, связан ли вопрос со снами
        is_dream_related = True
        if hasattr(self.dialog_manager, 'is_dream_related'):
            is_dream_related = self.dialog_manager.is_dream_related(message, history)
        
        # Если вопрос не о снах, возвращаем специальный ответ
        if not is_dream_related:
            return dedent(
                f"""
                Извини, {name}, но я специализируюсь на интерпретации снов. 
                
                Я могу помочь тебе разобраться в значении твоих снов, но не могу ответить на общие вопросы или вопросы, не связанные со снами.
                
                Расскажи, может быть, у тебя есть сон, который тебя беспокоит или интересует? Я буду рад помочь с его интерпретацией.
                """
            ).strip()
        
        # Более детальные ответы в зависимости от этапа
        if step.key == "greeting":
            age_text = ""
            if name != "друг" and age is not None:
                age_text = f" Учитывая твой возраст ({age} лет), я учту контекст для более точного анализа."
            
            return dedent(
                f"""
                Привет, {name}! Спасибо, что поделился своим сном. Я вижу, что тебе важно разобраться в его значении.{age_text}
                
                Сны часто отражают наши внутренние переживания и нерешённые вопросы. Давай вместе исследуем, что твой сон может рассказать о тебе.
                
                Расскажи, какие эмоции ты испытал во сне? Что особенно запомнилось?
                """
            ).strip()
        
        elif step.key == "exploration":
            keywords = ["эмоции", "ощущения", "детали", "контекст"]
            keyword = random.choice(keywords)
            return dedent(
                f"""
                Интересно, {name}. Чтобы лучше понять твой сон, мне важно узнать больше о {keyword}.
                
                Что ты чувствовал во сне? Было ли это страшно, тревожно, или наоборот — спокойно? 
                А что происходит в твоей жизни сейчас — есть ли что-то, что тебя беспокоит или радует?
                
                Эти детали помогут нам найти связь между сном и твоим внутренним состоянием.
                """
            ).strip()
        
        elif step.key == "analysis":
            interpretations = [
                "может отражать твои внутренние переживания",
                "возможно, связан с твоими неосознанными страхами или желаниями",
                "может быть отражением твоего текущего эмоционального состояния",
            ]
            interpretation = random.choice(interpretations)
            return dedent(
                f"""
                {name}, с психологической точки зрения, этот сон {interpretation}.
                
                Сны — это способ нашего подсознания общаться с нами. Они помогают нам увидеть то, что мы не замечаем в повседневной жизни.
                
                Попробуй подумать: есть ли в твоей жизни сейчас ситуации, которые вызывают похожие эмоции? Что ты можешь сделать, чтобы поддержать себя?
                """
            ).strip()
        
        else:  # closing
            return dedent(
                f"""
                {name}, спасибо за доверие. Надеюсь, наш разговор помог тебе лучше понять себя.
                
                Помни: сны — это инструмент самопознания. Продолжай обращать внимание на них, записывай свои сны и размышляй над ними.
                
                Я всегда готов продолжить наш разговор, когда у тебя появятся новые сны или вопросы.
                """
            ).strip()

    def interpret(
        self,
        user_profile: dict[str, str | None],
        message: str,
        history: List[dict[str, str]],
        previous_sessions: List[dict] | None = None,
        session_count: int = 0,
    ) -> tuple[str, str]:
        # Ранняя проверка: является ли сообщение связанным со снами
        is_dream_related = True
        if hasattr(self.dialog_manager, 'is_dream_related'):
            is_dream_related = self.dialog_manager.is_dream_related(message, history)
            logger.info(f"Message dream-related check: {is_dream_related} for message: {message[:50]}...")
        
        # Если сообщение не о снах, сразу возвращаем специальный ответ
        if not is_dream_related:
            # Но если это приветствие/small talk в начале - ответить дружелюбным приветствием
            msg_lower = (message or "").lower().strip()
            # Нормализуем: убираем пунктуацию, оставляем пробелы и буквы/цифры
            msg_norm = re.sub(r"[^a-zа-яё0-9\s]", " ", msg_lower)
            greeting_keywords = [
                "привет", "прив", "здравствуй", "здравствуйте", "здрасте",
                "добрый день", "добрый вечер", "доброе утро",
                "hello", "hi", "hey", "yo", "йо", "йоу", "салют"
            ]
            if any(k in msg_norm for k in greeting_keywords):
                step = None
                if hasattr(self.dialog_manager, 'get_step'):
                    step = self.dialog_manager.get_step("greeting")
                # Fallback: если по какой-то причине шага нет, используем greeting как ключ
                if step is None:
                    # Создаем минимальный объект-заменитель шага
                    class _TmpStep:
                        key = "greeting"
                    step = _TmpStep()  # type: ignore
                reply = self.fallback_response(step, message, user_profile, history)
                return reply, "greeting"
            
            # Вежливое прощание: если пользователь прощается, отвечаем теплым завершением, а не off-topic
            goodbye_keywords = [
                "пока", "до свидания", "прощай", "увидимся", "всего доброго", "доброй ночи",
                "спасибо, пока", "спасибо пока", "до встречи", "покеда", "бай",
                "bye", "goodbye", "see you"
            ]
            if any(k in msg_norm for k in goodbye_keywords):
                step = None
                if hasattr(self.dialog_manager, 'get_step'):
                    step = self.dialog_manager.get_step("closing")
                if step is None:
                    class _TmpStep:
                        key = "closing"
                    step = _TmpStep()  # type: ignore
                reply = self.fallback_response(step, message, user_profile, history)
                return reply, "closing"
            
            # Если это самое первое сообщение без признаков «про сны» — отвечаем теплым приветствием
            # вместо жёсткого off-topic отказа
            if not history:
                step = None
                if hasattr(self.dialog_manager, 'get_step'):
                    step = self.dialog_manager.get_step("greeting")
                if step is None:
                    class _TmpStep:
                        key = "greeting"
                    step = _TmpStep()  # type: ignore
                reply = self.fallback_response(step, message, user_profile, history)
                return reply, "greeting"
            
            name = user_profile.get("name") or "друг"
            off_topic_reply = (
                f"Извини, {name}, но я специализируюсь на интерпретации снов. "
                f"Я могу помочь тебе разобраться в значении твоих снов, но не могу ответить на общие вопросы или вопросы, не связанные со снами.\n\n"
                f"Расскажи, может быть, у тебя есть сон, который тебя беспокоит или интересует? Я буду рад помочь с его интерпретацией."
            )
            logger.info(f"Off-topic message detected, returning special response")
            return off_topic_reply, "greeting"
        
        prompt, step = self.build_prompt(
            user_profile, message, history, previous_sessions, session_count
        )
        llm_reply = self._call_gigachat(prompt)
        
        if llm_reply:
            # Валидируем ответ, если используем улучшенный менеджер
            if self.use_improved and hasattr(self.dialog_manager, 'validate_response'):
                is_valid, issues = self.dialog_manager.validate_response(llm_reply, step)
                if not is_valid:
                    logger.warning(f"Response validation failed for stage {step.key}: {issues}")
                    # Можно либо перегенерировать, либо использовать fallback
                    # Пока используем ответ, но логируем проблемы
                    logger.info(f"Using GigaChat response despite validation issues: {llm_reply[:100]}...")
                else:
                    logger.info(f"Response validated successfully for stage {step.key}")
            
            logger.info(f"Using GigaChat response for stage {step.key}")
            return llm_reply, step.key
        
        logger.info(f"Using fallback response for stage {step.key}")
        return self.fallback_response(step, message, user_profile, history), step.key

    def summarize_dream(
        self,
        conversation_turns: List[dict[str, str]],
        user_profile: dict[str, str | None] | None = None,
    ) -> str:
        """
        Строит краткое, структурированное резюме сна по истории диалога.
        Ожидает последовательность ходов вида {"user": "...", "bot": "..."} в хронологическом порядке.
        """
        name = (user_profile or {}).get("name") or "друг"
        # Соберем консолидированный текст пользователя
        user_texts = []
        for t in conversation_turns:
            txt = (t.get("user") or "").strip()
            if txt:
                user_texts.append(txt)
        consolidated_user_story = "\n".join(user_texts).strip()[:4000]  # ограничим размер
        if not consolidated_user_story:
            consolidated_user_story = "Пользователь не оставил явного описания сна."
        
        prompt = dedent(f"""
        Ты "ИИ Сонник" — эмпатичный психологический ассистент по интерпретации снов.
        
        ТЕБЕ НУЖНО СДЕЛАТЬ КОРОТКОЕ РЕЗЮМЕ СНА (5-8 предложений), включающее:
        1) Краткий сюжет сна (1-2 предложения).
        2) Основные эмоции и переживания.
        3) Возможные психологические смыслы и темы (без мистики).
        4) 1-2 практических шага для рефлексии.
        
        Пиши естественно, дружелюбно, на "ты". Используй имя "{name}" не более 1 раза.
        
        ОРИГИНАЛЬНОЕ ОПИСАНИЕ СНА (собранное из сообщений пользователя):
        ---
        {consolidated_user_story}
        ---
        
        ВЫВЕДИ ТОЛЬКО РЕЗЮМЕ, БЕЗ ПРЕАМБУЛ И ЗАКЛЮЧИТЕЛЬНЫХ ФРАЗ.
        """).strip()
        
        # Попытаемся получить ответ от LLM
        llm_reply = self._call_gigachat(prompt)
        if llm_reply:
            return llm_reply.strip()
        
        # Fallback: простая эвристическая выжимка
        # 1-2 предложения сюжета: первые 2 предложения из пользовательского текста
        sentences = [s.strip() for s in consolidated_user_story.replace("\n", " ").split(".") if s.strip()]
        plot = ". ".join(sentences[:2]) + ("." if sentences[:2] else "")
        # Базовая структура fallback-а
        fallback = dedent(f"""
        {name}, судя по твоему рассказу, сон затрагивает важные для тебя переживания. {plot}
        
        Эмоционально это может быть связано с внутренним напряжением или потребностью в опоре. 
        Возможно, сон отражает темы контроля, неопределенности или поиска ясности.
        
        Попробуй отметить, какие моменты во сне вызвали самые сильные эмоции, и есть ли похожие ситуации в реальности.
        Поддержи себя: выспись, сделай короткую запись сна и обрати внимание на повторяющиеся мотивы — они подскажут, что сейчас важно.
        """).strip()
        return fallback
