from typing import Dict, Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.database import ORM
from methods.text_builder import TextBuilder
from tgbot.keyboards.keyboards import Keyboard


class ORMMiddleware(BaseMiddleware):
    def __init__(self, orm: ORM):
        self.orm = orm

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["orm"] = self.orm
        data["keyboard"] = Keyboard()
        data["text_builder"] = TextBuilder()
        result = await handler(event, data)
        return result