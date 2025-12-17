"""Точка входа для Telegram-бота CodeHelper Bot на aiogram"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties  # type: ignore

from config import BOT_TOKEN
from handlers import menu_handlers, systems_conversion, codes_and_errors


async def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        print("Ошибка: BOT_TOKEN не установлен. Создайте файл .env и добавьте BOT_TOKEN=ваш_токен")
        return
    
    # Создать бота и диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)    
    
    # Регистрация роутеров (menu_handlers первым для приоритета кнопки Меню)
    dp.include_router(menu_handlers.router)
    dp.include_router(systems_conversion.router)
    dp.include_router(codes_and_errors.router)
    
    # Запуск бота
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
