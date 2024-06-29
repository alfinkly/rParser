from aiogram import Router, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.chat_action import ChatActionSender

from database.database import ORM
from database.models import Product, GeneralProduct
from methods.join_image import merge_images_square
from tgbot.keyboards.callbacks import HomeCallback, CategoryCallback
from tgbot.middlewares.keyboards import Keyboard
from tgbot.middlewares.texts import Text

router = Router()


@router.callback_query(CategoryCallback.filter())
async def category_button_click(callback: CallbackQuery,
                                callback_data: CategoryCallback,
                                keyboard: Keyboard,
                                texts: Text,
                                orm: ORM,
                                state: FSMContext):
    async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
        category_products = await orm.general_product_repo.select_by_general_category_id(callback_data.id)
        first_product = category_products[0]
        match_products: list[Product] = await \
            orm.general_product_repo.select_by_first_product_id(first_product.first_product_id)
        markup = keyboard.product_match(first_product.id)
        text = texts.build_general_product_text(match_products)
        image_url = FSInputFile(merge_images_square([p.image_url for p in match_products]))
        await state.set_data({"category_products": category_products})
        await callback.answer()
        # todo заменить функцию создания фото
        await callback.message.answer_photo(caption=text,
                                            reply_markup=markup,
                                            photo=image_url,
                                            parse_mode=ParseMode.HTML)
