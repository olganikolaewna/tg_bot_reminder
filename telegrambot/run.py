import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import TOKEN
from app.handlers import router
from app.database.models import async_main
from app.reminder_worker import reminder_worker


async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="начать работу"),
        BotCommand(command="help", description="помощь по боту"),
        BotCommand(command="edit_location", description="поменять местоположение"),
        BotCommand(command="about_me", description="узнать что умеет бот")
    ]
    await bot.set_my_commands(commands)


async def main():
    await async_main()
    bot = Bot(token=TOKEN)

    await setup_bot_commands(bot)

    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(reminder_worker(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')