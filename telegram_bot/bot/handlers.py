from __future__ import annotations

import base64
from datetime import datetime
from io import BytesIO

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from .integrations import ApiGatewayClient


STAGE_LABELS = {
    "greeting": "Приветствие",
    "exploration": "Исследование деталей",
    "analysis": "Анализ образов",
    "closing": "Завершение и рекомендации",
}


def format_reply_with_stage(reply: str, stage: str | None, hint: str | None) -> str:
    result = reply
    if stage and stage in STAGE_LABELS:
        result = f"📊 {STAGE_LABELS[stage]}\n\n{result}"
    if hint:
        result = f"{result}\n\n💡 Подсказка: {hint}"
    return result


def create_tts_keyboard(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Озвучить ответ", callback_data=f"tts_{message_id}")]
        ]
    )


def auth_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
    )


def parse_birth_date(date_str: str) -> str:
    """Парсит дату в формате ГГГГ-ММ-ДД или ДД.ММ.ГГГГ"""
    date_str = date_str.strip()
    
    if "." in date_str:
        parts = date_str.split(".")
        if len(parts) != 3:
            raise ValueError("Неверный формат даты. Используй ГГГГ-ММ-ДД или ДД.ММ.ГГГГ")
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        date_str = f"{year}-{month:02d}-{day:02d}"
    elif "-" not in date_str:
        raise ValueError("Неверный формат даты. Используй ГГГГ-ММ-ДД или ДД.ММ.ГГГГ")
    
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    if parsed_date > datetime.now().date():
        raise ValueError("Дата рождения не может быть в будущем")
    
    return date_str


def validate_phone(phone: str, gateway: ApiGatewayClient) -> str:
    """Валидирует и форматирует номер телефона"""
    formatted = gateway._format_phone(phone)
    if not formatted or not formatted.startswith("+7") or len(formatted) != 12 or not formatted[2:].isdigit():
        raise ValueError("Неверный формат номера телефона")
    return formatted


async def handle_phone_auth(message: Message, phone: str, gateway: ApiGatewayClient, pending_auth: set, manual_phone: set):
    """Обработка авторизации по номеру телефона"""
    user_id = message.from_user.id
    formatted_phone = validate_phone(phone, gateway)
    
    try:
        response = await gateway.login_with_phone(user_id=user_id, phone=formatted_phone)
        pending_auth.discard(user_id)
        manual_phone.discard(user_id)
        user_info = response.get("user", {})
        await message.answer(
            f"Авторизация успешно выполнена ✨\n\n"
            f"Имя: {user_info.get('name', 'Не указано')}\n"
            f"Телефон: {user_info.get('phone', formatted_phone)}\n\n"
            f"Можно делиться снами!",
            reply_markup=ReplyKeyboardRemove()
        )
    except ValueError as e:
        if "не найден" in str(e).lower():
            await message.answer(
                "Пользователь с таким номером не найден. 📝\n\n"
                "Используй /register для регистрации нового аккаунта.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                f"❌ Неверный формат номера телефона.\n\n"
                f"Пожалуйста, отправь номер в формате:\n"
                f"• +79991234567\n"
                f"• 89991234567\n"
                f"• 9991234567\n\n"
                f"Или поделись контактом из Telegram.",
                reply_markup=auth_keyboard(),
            )
        pending_auth.discard(user_id)
        manual_phone.discard(user_id)
    except Exception as e:
        await message.answer(f"Ошибка при авторизации: {str(e)}", reply_markup=ReplyKeyboardRemove())
        pending_auth.discard(user_id)
        manual_phone.discard(user_id)


async def handle_phone_register(message: Message, phone: str, gateway: ApiGatewayClient, reg_data: dict, pending_register: dict):
    """Обработка номера телефона при регистрации"""
    user_id = message.from_user.id
    formatted_phone = validate_phone(phone, gateway)
    
    try:
        reg_data["data"]["phone"] = formatted_phone
        response = await gateway.register(
            user_id=user_id,
            phone=formatted_phone,
            name=reg_data["data"]["name"],
            birth_date=reg_data["data"]["birth_date"],
        )
        pending_register.pop(user_id, None)
        
        user_info = response.get("user", {})
        await message.answer(
            f"Регистрация успешно завершена! ✨\n\n"
            f"Имя: {user_info.get('name', reg_data['data']['name'])}\n"
            f"Телефон: {user_info.get('phone', formatted_phone)}\n"
            f"Дата рождения: {user_info.get('birth_date', reg_data['data']['birth_date'])}\n\n"
            f"Можно делиться снами!",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        # Убеждаемся, что pending_register очищен при любой ошибке
        pending_register.pop(user_id, None)
        # Перебрасываем исключение для обработки в вызывающем коде
        raise


def register_handlers(dp: Dispatcher, gateway: ApiGatewayClient, bot, default_birth_date: str) -> None:
    pending_auth: set[int] = set()
    manual_phone: set[int] = set()
    pending_register: dict[int, dict] = {}

    @dp.message(Command("start"))
    async def start(message: Message) -> None:
        is_authorized = gateway.has_session(message.from_user.id)
        mode_text = "Личный кабинет" if is_authorized else "Гостевой режим"
        await message.answer(
            f"Привет! Я «ИИ Сонник» 🤍\n\n"
            f"Режим: {mode_text}\n\n"
            "Команды:\n"
            "• /register — регистрация (имя, дата рождения, телефон)\n"
            "• /auth — авторизация по номеру телефона\n"
            "• /profile — просмотр профиля\n"
            "• /clear — очистить историю снов\n"
            "• /support — поддержать проект\n"
            "• /logout — выйти\n\n"
            "Можешь сразу писать сон или отправлять голосовое — я помогу с интерпретацией! "
            "В гостевом режиме история не сохраняется, но можно попробовать бесплатно."
        )

    @dp.message(Command("register"))
    async def register(message: Message) -> None:
        user_id = message.from_user.id
        pending_register[user_id] = {"step": "name", "data": {}}
        await message.answer(
            "Начнём регистрацию! 📝\n\n"
            "Шаг 1 из 3: Как тебя зовут?\n"
            "Отправь своё имя.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Отмена")]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    @dp.message(Command("auth"))
    async def auth(message: Message) -> None:
        pending_auth.add(message.from_user.id)
        manual_phone.add(message.from_user.id)
        await message.answer(
            "Вход в аккаунт 🔐\n\n"
            "Отправь номер телефона текстом в формате +79991234567.\n\n"
            "Если у тебя ещё нет аккаунта, используй /register для регистрации.",
            reply_markup=auth_keyboard(),
        )

    @dp.message(Command("logout"))
    async def logout(message: Message) -> None:
        user_id = message.from_user.id
        profile_data = await gateway.get_user_profile(user_id)
        user_name = profile_data.get("name", "Друг") if profile_data else "Друг"
        gateway.logout(user_id)
        await message.answer(
            f"👋 {user_name}, ты вышел из аккаунта.\n\n"
            f"Для входа используй /auth",
            reply_markup=ReplyKeyboardRemove()
        )

    @dp.message(Command("profile"))
    async def profile(message: Message) -> None:
        user_id = message.from_user.id
        if not gateway.has_session(user_id):
            await message.answer("Вы в гостевом режиме. Для просмотра профиля авторизуйтесь через /auth.")
            return
        
        profile_data = await gateway.get_user_profile(user_id)
        if not profile_data:
            await message.answer("Не удалось загрузить профиль.")
            return
        
        await message.answer(
            f"👤 Профиль\n\n"
            f"Имя: {profile_data.get('name', 'Не указано')}\n"
            f"Телефон: {profile_data.get('phone', 'Не указано')}\n"
            f"Дата рождения: {profile_data.get('birth_date', 'Не указано')}\n"
        )

    @dp.message(Command("clear"))
    async def clear(message: Message) -> None:
        user_id = message.from_user.id
        if not gateway.has_session(user_id):
            await message.answer("В гостевом режиме история не сохраняется. Для очистки истории авторизуйтесь через /auth.")
            return
        try:
            await gateway.delete_sessions(user_id)
            await message.answer("История диалога очищена. Начнём новый разговор?")
        except Exception as e:
            await message.answer(f"❌ Ошибка при очистке истории: {str(e)}")

    @dp.message(Command("support"))
    async def support(message: Message) -> None:
        user_id = message.from_user.id
        if not gateway.has_session(user_id):
            await message.answer("Для поддержки проекта необходимо авторизоваться через /auth.")
            return
        
        try:
            link = await gateway.request_support_link(user_id, amount=199.0)
            await message.answer(
                f"💚 Спасибо за желание поддержать проект!\n\n"
                f"Перейди по ссылке для оплаты:\n{link}\n\n"
                f"Стандартная сумма: 199₽ (можно изменить на странице оплаты)"
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка при создании ссылки на оплату: {str(e)}")

    # Удалён обработчик контакта: ввод телефона допускается только вручную

    @dp.message(F.text.lower() == "отмена")
    async def cancel(message: Message) -> None:
        user_id = message.from_user.id
        pending_auth.discard(user_id)
        manual_phone.discard(user_id)
        pending_register.pop(user_id, None)
        await message.answer("Операция отменена.", reply_markup=ReplyKeyboardRemove())

    @dp.message(F.text.regexp(r"^\+?\d{6,15}$"))
    async def manual_phone_handler(message: Message) -> None:
        user_id = message.from_user.id
        
        # Не обрабатывать телефон, если пользователь в процессе регистрации на других шагах
        if user_id in pending_register:
            reg_data = pending_register[user_id]
            # Если это шаг "birth_date", это не телефон, а ошибка ввода даты
            if reg_data["step"] == "birth_date":
                await message.answer(
                    "❌ Неверный формат даты. Используй ГГГГ-ММ-ДД (например, 1990-01-15) или ДД.ММ.ГГГГ (например, 15.01.1990)",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Отмена")]],
                        resize_keyboard=True,
                        one_time_keyboard=True,
                    ),
                )
                return
            # Если это шаг "phone", обработать как телефон при регистрации
            if reg_data["step"] == "phone":
                try:
                    await handle_phone_register(message, message.text, gateway, reg_data, pending_register)
                except ValueError:
                    await message.answer(
                        "❌ Неверный формат номера телефона.\n\n"
                        "Отправь номер в формате +79991234567.",
                        reply_markup=auth_keyboard(),
                    )
                except Exception as e:
                    error_msg = str(e)
                    if "уже зарегистрирован" in error_msg or "already registered" in error_msg.lower():
                        await message.answer("Пользователь с таким номером уже зарегистрирован. Используй /auth для входа.", reply_markup=ReplyKeyboardRemove())
                    else:
                        await message.answer(f"❌ Ошибка при регистрации: {error_msg}", reply_markup=ReplyKeyboardRemove())
                    pending_register.pop(user_id, None)
                return
            # Для других шагов регистрации не обрабатывать как телефон
            return
        
        # Обрабатывать как телефон только если пользователь ожидает ввода телефона для авторизации
        if user_id not in manual_phone:
            return
        
        await handle_phone_auth(message, message.text, gateway, pending_auth, manual_phone)

    @dp.callback_query(F.data.startswith("tts_"))
    async def handle_tts_callback(callback: CallbackQuery) -> None:
        await callback.answer("Генерирую аудио...")
        
        message_text = callback.message.text or callback.message.caption or ""
        lines = message_text.split("\n")
        clean_lines = [line for i, line in enumerate(lines) 
                      if not (line.startswith("📊") or line.startswith("💡") or 
                             (i > 0 and not line.strip() and (lines[i-1].startswith("📊") or lines[i-1].startswith("💡"))))]
        clean_text = "\n".join(clean_lines).strip()
        
        if not clean_text:
            await callback.answer("Не удалось получить текст для озвучки", show_alert=True)
            return
        
        try:
            audio_data = await gateway.text_to_speech(clean_text, lang="ru")
            audio_file = BytesIO(audio_data)
            audio_file.name = "response.ogg"
            await callback.message.answer_voice(voice=audio_file, caption="Озвучка ответа")
        except Exception as e:
            await callback.answer(f"Ошибка озвучки: {str(e)}", show_alert=True)

    @dp.message(F.content_type.in_({"text", "voice"}))
    async def handle_message(message: Message) -> None:
        user = message.from_user
        user_id = user.id

        if message.voice:
            try:
                file = await bot.get_file(message.voice.file_id)
                buffer = BytesIO()
                await bot.download_file(file.file_path, buffer)
                audio_base64 = base64.b64encode(buffer.getvalue()).decode()
                text = await gateway.transcribe_audio(user_id, audio_base64)
                if not text:
                    await message.answer("Не удалось распознать голос. Попробуйте ещё раз.")
                    return
            except Exception as e:
                await message.answer(f"❌ Ошибка при обработке голосового сообщения: {str(e)}")
                return
            
            guest_profile = None
            if not gateway.has_session(user_id):
                guest_profile = {"name": user.full_name or "Гость", "birth_date": None}
            
            try:
                data = await gateway.send_chat(user_id=user_id, text=text, guest_profile=guest_profile)
                formatted_reply = format_reply_with_stage(data.get("reply", "Не удалось получить ответ."), data.get("stage"), data.get("hint"))
                
                if not gateway.has_session(user_id):
                    formatted_reply += "\n\n💡 Используй /auth, чтобы сохранить историю снов."
                
                await message.answer(formatted_reply, reply_markup=create_tts_keyboard(message.message_id))
            except Exception as e:
                await message.answer(f"❌ Ошибка при отправке сообщения: {str(e)}")
            return

        if not message.text:
            await message.answer("Пожалуйста, отправь текст или голосовое сообщение.")
            return

        if user_id in pending_register:
            reg_data = pending_register[user_id]
            
            if reg_data["step"] == "name":
                name_text = (message.text or "").strip()
                # Минимальная проверка имени: не должно состоять только из цифр
                if not name_text or name_text.isdigit():
                    await message.answer(
                        "❌ Имя не может состоять только из цифр. Пожалуйста, введите имя буквами.",
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[[KeyboardButton(text="Отмена")]],
                            resize_keyboard=True,
                            one_time_keyboard=True,
                        ),
                    )
                    return
                reg_data["data"]["name"] = name_text
                reg_data["step"] = "birth_date"
                await message.answer(
                    f"Отлично, {reg_data['data']['name']}! 👋\n\n"
                    f"Шаг 2 из 3: Когда ты родился?\n"
                    f"Отправь дату рождения в формате ГГГГ-ММ-ДД (например, 1990-01-15)\n"
                    f"или ДД.ММ.ГГГГ (например, 15.01.1990)",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Отмена")]],
                        resize_keyboard=True,
                        one_time_keyboard=True,
                    ),
                )
                return
            
            elif reg_data["step"] == "birth_date":
                # Проверяем, не является ли сообщение телефоном (только цифры, длина 6-15)
                # Если это похоже на телефон, но не на дату, предупредить
                if message.text and message.text.replace("+", "").isdigit() and 6 <= len(message.text.replace("+", "")) <= 15:
                    await message.answer(
                        "❌ Это похоже на номер телефона, а не на дату рождения.\n\n"
                        "Используй формат ГГГГ-ММ-ДД (например, 1990-01-15) или ДД.ММ.ГГГГ (например, 15.01.1990)\n\n"
                        "Номер телефона введёшь на следующем шаге.",
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[[KeyboardButton(text="Отмена")]],
                            resize_keyboard=True,
                            one_time_keyboard=True,
                        ),
                    )
                    return
                
                try:
                    birth_date = parse_birth_date(message.text)
                    reg_data["data"]["birth_date"] = birth_date
                    reg_data["step"] = "phone"
                    await message.answer(
                        f"Отлично! ✅\n\n"
                        f"Шаг 3 из 3: Номер телефона 📱\n\n"
                        f"Отправь номер телефона текстом в формате:\n"
                        f"• +79991234567\n"
                        f"• 89991234567\n"
                        f"• 9991234567",
                        reply_markup=auth_keyboard(),
                    )
                except ValueError as e:
                    await message.answer(
                        f"❌ {str(e)}\n\n"
                        f"Попробуй ещё раз. Примеры: 1990-01-15 или 15.01.1990",
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[[KeyboardButton(text="Отмена")]],
                            resize_keyboard=True,
                            one_time_keyboard=True,
                        ),
                    )
                return
            
            elif reg_data["step"] == "phone":
                # Шаг "phone" обрабатывается в manual_phone_handler или contact handler
                # Если дошли сюда, значит сообщение не является телефоном
                await message.answer(
                    "❌ Ожидается номер телефона.\n\n"
                    "Поделись номером телефона из Telegram или отправь его текстом в формате:\n"
                    "• +79991234567\n"
                    "• 89991234567\n"
                    "• 9991234567",
                    reply_markup=auth_keyboard(),
                )
                return
        
        # Если пользователь в процессе регистрации, но шаг не обработан выше, не продолжать
        if user_id in pending_register:
            return
        
        # Обработка ручного ввода телефона для авторизации
        # Проверяем только если пользователь ожидает ввода телефона
        if user_id in manual_phone and message.text not in ("Отмена", "отмена"):
            # Этот вызов не нужен, так как manual_phone_handler уже зарегистрирован как обработчик
            # Но оставляем для обработки текстовых сообщений, которые не соответствуют регулярке
            # (например, если пользователь ввел телефон в неправильном формате)
            # В этом случае manual_phone_handler не сработает, поэтому обрабатываем здесь
            if message.text and message.text.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
                await message.answer(
                    "❌ Неверный формат номера телефона.\n\n"
                    "Используй формат:\n"
                    "• +79991234567\n"
                    "• 89991234567\n"
                    "• 9991234567\n\n"
                    "Отправь номер вручную.",
                    reply_markup=auth_keyboard(),
                )
            else:
                await message.answer(
                    "❌ Ожидается номер телефона.\n\n"
                    "Отправь номер телефона текстом в формате +79991234567.",
                    reply_markup=auth_keyboard(),
                )
            return

        guest_profile = None
        if not gateway.has_session(user_id):
            guest_profile = {"name": user.full_name or "Гость", "birth_date": None}
        
        try:
            data = await gateway.send_chat(user_id=user_id, text=message.text, guest_profile=guest_profile)
            formatted_reply = format_reply_with_stage(data.get("reply", "Не удалось получить ответ."), data.get("stage"), data.get("hint"))
            
            if not gateway.has_session(user_id):
                formatted_reply += "\n\n💡 Используй /auth, чтобы сохранить историю снов."
            
            await message.answer(formatted_reply, reply_markup=create_tts_keyboard(message.message_id))
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке сообщения: {str(e)}")
