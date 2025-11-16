from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from ..config import settings
from .handlers import register_handlers
from .integrations import ApiGatewayClient


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    gateway = ApiGatewayClient(settings.api_gateway_url)
    register_handlers(dp, gateway, bot, settings.default_birth_date)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Начать общение"),
            BotCommand(command="register", description="Регистрация нового аккаунта"),
            BotCommand(command="auth", description="Авторизация по номеру"),
            BotCommand(command="profile", description="Просмотр профиля"),
            BotCommand(command="clear", description="Очистить историю"),
            BotCommand(command="support", description="Поддержать проект"),
            BotCommand(command="logout", description="Выйти из профиля"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
