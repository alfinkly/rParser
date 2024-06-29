from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database.config import EnvSettings
from database.database import ORM
from tgbot.handlers import home, auth, category
from tgbot.middlewares.middleware import MainMiddleware


async def run_tgbot(orm: ORM):
    config = EnvSettings()
    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.message.middleware(MainMiddleware(orm))
    dp.callback_query.middleware(MainMiddleware(orm))
    dp.inline_query.middleware(MainMiddleware(orm))
    dp.include_routers(home.router, auth.router, category.router)
    await dp.start_polling(bot)