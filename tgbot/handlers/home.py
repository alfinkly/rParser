from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from database.database import ORM
from tgbot.handlers.states import AuthState
from tgbot.keyboards.callbacks import HomeCallback
from tgbot.middlewares.keyboards import Keyboard
from tgbot.middlewares.texts import Text

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, orm: ORM, keyboard: Keyboard):
    existing_user = await orm.user_repo.find_user_by_tgid(message.from_user.id)
    if existing_user:
        markup = keyboard.home()
        await message.answer("Привет Я бот для сравнения товаров из разных магазинов 👋🏻",
                             reply_markup=markup)
    else:
        keyboard = keyboard.send_phone()
        await state.set_state(AuthState.wait_contact)
        await message.answer("Для продолжения работы с ботом, поделитесь вашим номером телефона по кнопке ниже. 🔽",
                             reply_markup=keyboard)


@router.callback_query(HomeCallback.filter(F.action == "category"))
async def handler(callback: CallbackQuery, keyboard: Keyboard, orm: ORM, texts: Text):
    async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
        general_categories = await orm.general_category_repo.select_all()
        markup = keyboard.categories(general_categories)
        await callback.answer()
        await callback.message.delete()
        await callback.message.answer(text=texts.get("category.message"), reply_markup=markup)