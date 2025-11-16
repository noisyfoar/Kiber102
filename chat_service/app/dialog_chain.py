"""
Улучшенное диалоговое дерево с использованием LangChain для структурированных ответов.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

try:
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Создаем заглушки для BaseModel и Field
    class BaseModel:
        pass
    Field = None


@dataclass(frozen=True)
class DialogStep:
    """Этап диалога с четкими правилами и структурой."""
    key: str
    system_prompt: str
    follow_up: str
    hint: str
    required_elements: List[str]  # Обязательные элементы в ответе
    forbidden_elements: List[str]  # Запрещенные элементы


# DreamResponse будет использоваться только если LangChain доступен
# Пока оставляем как заглушку для будущего использования
if LANGCHAIN_AVAILABLE:
    class DreamResponse(BaseModel):
        """Структурированный ответ для валидации."""
        main_response: str = Field(description="Основной ответ пользователю (2-3 абзаца)")
        questions: List[str] = Field(default_factory=list, description="Вопросы для уточнения (если нужны)")
        practical_steps: List[str] = Field(default_factory=list, description="Практические шаги для рефлексии")
        emotional_tone: str = Field(description="Эмоциональный тон ответа: supportive, analytical, encouraging")
else:
    DreamResponse = None


# Улучшенные этапы диалога с четкими правилами
IMPROVED_STEPS: List[DialogStep] = [
    DialogStep(
        key="greeting",
        system_prompt=(
            "Ты эмпатичный психологический ассистент для интерпретации снов. "
            "Твоя задача - создать доверительную атмосферу и мотивировать пользователя поделиться сном. "
            "Будь теплым, но не навязчивым. Используй имя пользователя естественно."
        ),
        follow_up=(
            "Поприветствуй пользователя по имени. "
            "Поблагодари за доверие. "
            "Спроси, какой сон его сегодня особенно зацепил или беспокоит. "
            "НЕ давай интерпретацию на этом этапе - только слушай."
        ),
        hint="Расскажи о своем сне: что ты видел, какие эмоции испытывал?",
        required_elements=["приветствие", "благодарность", "вопрос о сне"],
        forbidden_elements=["интерпретация", "анализ", "советы"],
    ),
    DialogStep(
        key="exploration",
        system_prompt=(
            "Ты помогаешь пользователю детально описать сон. "
            "Задавай открытые вопросы, которые помогут понять эмоции, контекст и детали. "
            "Избегай наводящих вопросов - пусть пользователь сам рассказывает."
        ),
        follow_up=(
            "Уточни ключевые детали сна: "
            "1. Где происходило действие? "
            "2. Кто был рядом? "
            "3. Какие эмоции испытывал пользователь? "
            "4. Что происходило в его жизни накануне? "
            "Задай 1-2 конкретных вопроса для прояснения. "
            "НЕ давай интерпретацию - только собирай информацию."
        ),
        hint="Опиши детали: где происходило действие? Кто был рядом? Что ты чувствовал?",
        required_elements=["вопросы для уточнения", "просьба описать детали"],
        forbidden_elements=["интерпретация", "выводы", "советы"],
    ),
    DialogStep(
        key="analysis",
        system_prompt=(
            "Ты даешь психологическую интерпретацию сна БЕЗ эзотерики и мистики. "
            "Используй только научный психологический подход. "
            "Связывай сон с реальной жизнью пользователя, его эмоциями и переживаниями."
        ),
        follow_up=(
            "Дай психологическую интерпретацию сна: "
            "1. Что сон может отражать в реальной жизни пользователя? "
            "2. Какие эмоции или переживания он символизирует? "
            "3. Есть ли связь с текущей жизненной ситуацией? "
            "Будь конкретным, но не директивным. "
            "Предложи 1-2 практических шага для рефлексии."
        ),
        hint="Подумай: есть ли связь с твоей текущей жизненной ситуацией?",
        required_elements=["интерпретация", "связь с реальностью", "практические шаги"],
        forbidden_elements=["мистика", "эзотерика", "гадание", "предсказания"],
    ),
    DialogStep(
        key="closing",
        system_prompt=(
            "Ты завершаешь разговор, подводя итоги и поддерживая пользователя. "
            "Покажи, что разговор был полезен. "
            "Пригласи вернуться, но не навязывай."
        ),
        follow_up=(
            "Подведи краткие итоги разговора (1-2 предложения). "
            "Поддержи пользователя. "
            "Пригласи вернуться с новыми снами или вопросами. "
            "Будь теплым, но не навязчивым."
        ),
        hint="Хочешь обсудить еще что-то или задать вопрос?",
        required_elements=["итоги", "поддержка", "приглашение вернуться"],
        forbidden_elements=["новые вопросы", "глубокая интерпретация"],
    ),
]


class ImprovedDialogManager:
    """Улучшенный менеджер диалогов с валидацией и структурированием."""
    
    def __init__(self, steps: List[DialogStep] | None = None):
        self.steps = steps or IMPROVED_STEPS
        self.use_langchain = LANGCHAIN_AVAILABLE
    
    def get_step(self, key: str) -> Optional[DialogStep]:
        """Получить этап по ключу."""
        for step in self.steps:
            if step.key == key:
                return step
        return None
    
    def is_dream_related(self, message: str, history: List[dict[str, str]]) -> bool:
        """Определяет, является ли сообщение связанным со снами."""
        msg_lower = message.lower().strip()
        
        # Ключевые слова, связанные со снами
        dream_keywords = [
            'сон', 'сны', 'сновидение', 'сновидения', 'приснилось', 'приснился', 
            'приснилась', 'приснились', 'видел во сне', 'видела во сне',
            'снилось', 'снился', 'снилась', 'снились', 'сонник', 'интерпретация',
            'значение сна', 'что значит сон', 'объясни сон', 'толкование', 'толковать',
            'расшифровать', 'расшифровка', 'объясни что значит', 'что означает',
            'во сне', 'во снах', 'мой сон', 'мои сны', 'этот сон', 'эти сны'
        ]
        
        # ПРИОРИТЕТ 1: Если в сообщении есть ключевые слова о снах - точно релевантно
        if any(keyword in msg_lower for keyword in dream_keywords):
            return True
        
        # ПРИОРИТЕТ 2: Если есть история с упоминаниями снов - считаем релевантным
        # (даже если текущее сообщение не содержит явных ключевых слов)
        if history:
            history_text = ' '.join([h.get('user', '') + ' ' + h.get('bot', '') for h in history[-3:]])
            history_lower = history_text.lower()
            if any(keyword in history_lower for keyword in dream_keywords):
                # Если в истории были сны, то продолжение диалога релевантно
                # Исключение: явно общие вопросы без контекста
                return True
        
        # ПРИОРИТЕТ 3: Проверяем на явно общие вопросы (не связанные со снами)
        # Убрали слишком общие слова типа "объясни", "расскажи", "что это" - они могут быть в вопросах о снах
        general_questions = [
            'как дела', 'что нового', 'как жизнь', 'что делаешь', 'как поживаешь',
            'который час', 'какая погода', 'что на ужин', 'что приготовить',
            'как приготовить', 'рецепт', 'где купить', 'сколько стоит',
            'кто такой', 'когда', 'где находится', 'как добраться',
            'привет', 'здравствуй', 'добрый день', 'добрый вечер', 'доброе утро'
        ]
        
        # Если это явно общий вопрос БЕЗ упоминания снов И БЕЗ истории о снах
        if any(question in msg_lower for question in general_questions):
            # Если нет истории - точно не о снах
            if not history:
                return False
            # Если есть история, но в ней нет упоминаний снов - не о снах
            history_text = ' '.join([h.get('user', '') + ' ' + h.get('bot', '') for h in history[-3:]])
            history_lower = history_text.lower()
            if not any(keyword in history_lower for keyword in dream_keywords):
                return False
        
        # ПРИОРИТЕТ 4: Если сообщение очень короткое (менее 15 символов) и нет ключевых слов
        if len(message.strip()) < 15:
            if not history:
                return False
            # Проверяем историю
            history_text = ' '.join([h.get('user', '') + ' ' + h.get('bot', '') for h in history[-2:]])
            history_lower = history_text.lower()
            if not any(keyword in history_lower for keyword in dream_keywords):
                return False
        
        # ПРИОРИТЕТ 5: Если это первое сообщение без ключевых слов - вероятно не о снах
        if not history:
            return False
        
        # ПРИОРИТЕТ 6: По умолчанию для сообщений с историей - считаем релевантным
        # (если дошли до сюда, значит есть история, но нет явных признаков off-topic)
        return True
    
    def analyze_message(self, message: str, history: List[dict[str, str]]) -> dict:
        """Анализирует сообщение для определения следующего шага."""
        msg_lower = message.lower()
        msg_length = len(message)
        turn_count = len(history)
        
        analysis = {
            "has_question": any(word in msg_lower for word in ['почему', 'что значит', 'как понять', 'объясни', 'что это']),
            "has_details": msg_length > 150,
            "has_greeting": any(word in msg_lower for word in ['привет', 'здравствуй', 'добрый']),
            "has_thanks": any(word in msg_lower for word in ['спасибо', 'понял', 'ясно', 'благодарю']),
            "has_goodbye": any(word in msg_lower for word in ['до свидания', 'пока', 'увидимся']),
            "is_dream_related": self.is_dream_related(message, history),
            "turn_count": turn_count,
        }
        
        return analysis
    
    def next_step(
        self, history: List[dict[str, str]], user_message: str = ""
    ) -> DialogStep:
        """Определяет следующий этап на основе анализа сообщения."""
        if not history:
            return self.get_step("greeting") or self.steps[0]
        
        analysis = self.analyze_message(user_message, history)
        current_step = self.stage_for_turn(len(history) - 1)
        
        # Правила перехода между этапами
        if current_step.key == "greeting":
            if analysis["has_question"] or analysis["has_details"]:
                # Пользователь сразу задал вопрос или дал детали
                return self.get_step("exploration") or self.steps[1]
        
        if current_step.key == "exploration":
            if analysis["has_question"] and analysis["has_details"]:
                # Пользователь дал детали и просит интерпретацию
                return self.get_step("analysis") or self.steps[2]
            elif analysis["turn_count"] >= 2 and analysis["has_details"]:
                # Достаточно информации для анализа
                return self.get_step("analysis") or self.steps[2]
        
        if current_step.key == "analysis":
            if analysis["has_thanks"] or analysis["has_goodbye"]:
                return self.get_step("closing") or self.steps[3]
            elif analysis["turn_count"] >= 3:
                # После анализа можно завершать
                return self.get_step("closing") or self.steps[3]
        
        # По умолчанию следуем линейному флоу
        return self.stage_for_turn(len(history))
    
    def stage_for_turn(self, turn_index: int) -> DialogStep:
        """Получить этап по индексу хода."""
        idx = min(turn_index, len(self.steps) - 1)
        return self.steps[idx]
    
    def build_structured_prompt(
        self,
        step: DialogStep,
        user_profile: dict[str, str | None],
        message: str,
        history: List[dict[str, str]],
        emotion: str,
        previous_sessions: List[dict] | None = None,
        age: int | None = None,
        is_dream_related: bool = True,
    ) -> str:
        """Строит структурированный промпт с четкими правилами."""
        name = user_profile.get('name') or 'друг'
        
        # История диалога
        history_text = ""
        if history:
            history_text = "\n".join(
                f"Пользователь: {item['user']}\nСонник: {item['bot']}" 
                for item in reversed(history[-3:])
            )
        else:
            history_text = "Это начало разговора."
        
        # Если вопрос не о снах, добавляем специальную инструкцию
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
        
        # Правила для этапа
        rules = f"""
ОБЯЗАТЕЛЬНО включи в ответ:
{chr(10).join(f"- {elem}" for elem in step.required_elements)}

НИКОГДА не включай:
{chr(10).join(f"- {elem}" for elem in step.forbidden_elements)}
"""
        
        # Эмоциональный контекст
        emotion_guidance = ""
        if emotion == "negative":
            emotion_guidance = (
                "\n⚠️ ВАЖНО: Пользователь испытывает тревогу. "
                "Будь особенно поддерживающим и мягким. "
                "Не усугубляй тревогу. Фокусируйся на поддержке, а не на глубоком анализе."
            )
        elif emotion == "positive":
            emotion_guidance = "\n✅ Пользователь в позитивном настроении. Поддержи это состояние."
        
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
        
        # Контекст возраста
        age_context = ""
        if age is not None:
            age_context = f"\n- Возраст пользователя: {age} лет (учитывай возрастной контекст при интерпретации)"
        
        prompt = f"""
Ты "ИИ Сонник" — эмпатичный психологический ассистент для интерпретации снов.

{off_topic_guidance}

{step.system_prompt}

ЭТАП ДИАЛОГА: {step.key}

ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
{step.follow_up}

{rules}

{emotion_guidance}
{personalized_greeting}

КОНТЕКСТ:
- Имя пользователя: {name}{age_context}
- История диалога:
{history_text}

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {message}

ОТВЕТЬ:
1. Строго следуй правилам этапа {step.key}
2. Включи все обязательные элементы
3. Избегай запрещенных элементов
4. Будь конкретным и релевантным
5. Длина: 2-4 абзаца (не больше!)
6. Говори на "ты", дружелюбно
7. Используй имя "{name}" естественно (1-2 раза)

Помни: Твой ответ должен быть ПО ДЕЛУ, релевантным сообщению пользователя и этапу диалога.
"""
        return prompt.strip()
    
    def validate_response(self, response: str, step: DialogStep) -> tuple[bool, List[str]]:
        """Валидирует ответ на соответствие правилам этапа."""
        response_lower = response.lower()
        issues = []
        
        # Проверяем обязательные элементы
        for required in step.required_elements:
            if required not in response_lower:
                issues.append(f"Отсутствует обязательный элемент: {required}")
        
        # Проверяем запрещенные элементы
        for forbidden in step.forbidden_elements:
            if forbidden in response_lower:
                issues.append(f"Обнаружен запрещенный элемент: {forbidden}")
        
        # Проверяем длину
        if len(response) < 100:
            issues.append("Ответ слишком короткий")
        elif len(response) > 1000:
            issues.append("Ответ слишком длинный")
        
        return len(issues) == 0, issues

