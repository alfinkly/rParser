from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.database import ORM
from tgbot.handlers.home import cmd_start
from tgbot.handlers.states import AuthState
from tgbot.middlewares.keyboards import Keyboard

router = Router()


@router.message(F.contact, AuthState.wait_contact)
async def contact_received(message: Message, state: FSMContext, orm: ORM, keyboard: Keyboard):
    await orm.user_repo.insert_or_update(message)
    await message.answer("Спасибо за предоставленную информацию!")
    await cmd_start(message, state, orm, keyboard)