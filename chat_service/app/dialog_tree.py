from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DialogStep:
    key: str
    system_prompt: str
    follow_up: str
    hint: str  # Подсказка для пользователя


STEPS: List[DialogStep] = [
    DialogStep(
        key="greeting",
        system_prompt="Поприветствуй пользователя по имени и поблагодари за доверие. НЕ давай интерпретацию на этом этапе.",
        follow_up="Спроси, какой сон сегодня его особенно зацепил. Только слушай, не анализируй.",
        hint="Расскажи о своем сне: что ты видел, какие эмоции испытывал?",
    ),
    DialogStep(
        key="exploration",
        system_prompt="Уточни ключевые детали сна: эмоции, образы, контекст жизни. НЕ давай интерпретацию - только собирай информацию.",
        follow_up="Сформулируй 1–2 конкретных вопроса для прояснения: где происходило действие? Кто был рядом? Что чувствовал пользователь?",
        hint="Опиши детали: где происходило действие? Кто был рядом? Что ты чувствовал?",
    ),
    DialogStep(
        key="analysis",
        system_prompt="Дай психологическую интерпретацию БЕЗ эзотерики и мистики. Связывай сон с реальной жизнью пользователя.",
        follow_up="Объясни, что сон может отражать в реальной жизни. Предложи 1-2 практических шага для рефлексии. Будь конкретным.",
        hint="Подумай: есть ли связь с твоей текущей жизненной ситуацией?",
    ),
    DialogStep(
        key="closing",
        system_prompt="Подведи итоги разговора и поддержи пользователя.",
        follow_up="Пригласи вернуться с новыми снами.",
        hint="Хочешь обсудить еще что-то или задать вопрос?",
    ),
]


class DialogManager:
    def __init__(self, steps: List[DialogStep] | None = None) -> None:
        self.steps = steps or STEPS

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

    def stage_for_turn(self, turn_index: int) -> DialogStep:
        idx = min(turn_index, len(self.steps) - 1)
        return self.steps[idx]

    def should_advance_stage(
        self, current_step: DialogStep, history: List[dict[str, str]], user_message: str
    ) -> bool:
        """Определяет, нужно ли переходить на следующий этап на основе контекста."""
        msg_lower = user_message.lower()
        
        # Если пользователь задает вопрос о значении - переходим к exploration
        if current_step.key == "greeting":
            if any(word in msg_lower for word in ['почему', 'что значит', 'как понять', 'объясни']):
                return True
        
        # Если пользователь дал достаточно деталей - переходим к анализу
        if current_step.key == "exploration":
            if len(user_message) > 150 and len(history) >= 1:
                return True
            # Если пользователь явно просит интерпретацию
            if any(word in msg_lower for word in ['что это значит', 'интерпретация', 'объясни']):
                return True
        
        # Если пользователь благодарит или прощается - переходим к завершению
        if current_step.key == "analysis":
            if any(word in msg_lower for word in ['спасибо', 'понял', 'ясно', 'до свидания']):
                return True
        
        return False

    def next_step(
        self, history: List[dict[str, str]], user_message: str = ""
    ) -> DialogStep:
        """Определяет следующий этап на основе истории и последнего сообщения пользователя."""
        turn_count = len(history)
        
        # Если есть история, проверяем текущий этап
        if turn_count > 0:
            current_step = self.stage_for_turn(turn_count - 1)
            
            # Проверяем, нужно ли перейти на следующий этап
            if self.should_advance_stage(current_step, history, user_message):
                next_idx = min(
                    self.steps.index(current_step) + 1, len(self.steps) - 1
                )
                return self.steps[next_idx]
        
        # Иначе следуем линейному флоу
        return self.stage_for_turn(turn_count)
