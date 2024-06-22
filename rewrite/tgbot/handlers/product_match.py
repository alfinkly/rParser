import hashlib
import os

from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from database.database import ORM
from database.models import Product, ProductMatch
from methods.join_image import merge_images_square
from methods.text_builder import TextBuilder
from tgbot.keyboards.callbacks import ProductMatchCallback, ProductCallback, HomeCallback
from tgbot.keyboards.keyboards import Keyboard

router = Router()


@router.callback_query(HomeCallback.filter(F.action == "matches"))
async def product_match_callback(callback: CallbackQuery, orm: ORM, state: FSMContext, keyboard: Keyboard,
                                 text_builder: TextBuilder):
    products_match: list[ProductMatch] = await orm.product_match_repo.select_all()

    if not products_match:
        await callback.answer("No products found.", show_alert=True)
        return

    unique_products = await orm.product_match_repo.select_unique_first_product_ids()
    products: list[Product] = await orm.product_match_repo.select_by_first_product_id(unique_products[0])
    text = f"Совпадение товаров 1/{len(unique_products)}\n"
    text += text_builder.build_product_match_text(products)
    markup = keyboard.product_match()

    image_path = merge_images_square([p.image_url for p in products])
    await callback.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(image_path),
                                  caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
    os.remove(image_path)
    await state.update_data({"now_product_id": 0, "max_id_pm": len(products_match) - 1,
                             "unique_products": unique_products})
    await callback.answer()


# Обработка нажатий кнопок "next"
@router.callback_query(ProductMatchCallback.filter(F.action == "next"))
async def product_button_callback(callback: CallbackQuery, callback_data: ProductCallback, orm: ORM, state: FSMContext,
                                  keyboard: Keyboard, text_builder: TextBuilder):
    data = await state.get_data()
    now_product = data.get("now_product_id", 0)
    max_id_pm = data.get("max_id_pm")
    unique_products = data.get("unique_products")

    now_product += 1
    if now_product > max_id_pm:
        now_product = 0

    products: list[Product] = await orm.product_match_repo.select_by_first_product_id(unique_products[now_product])

    text = f"Совпадение товаров {now_product + 1}/{len(unique_products)}\n"
    text += text_builder.build_product_match_text(products)

    markup = keyboard.product_match()

    image_path = merge_images_square([p.image_url for p in products])
    await callback.message.answer_photo(photo=FSInputFile(image_path), caption=text, parse_mode=ParseMode.HTML,
                                        reply_markup=markup)
    await callback.message.delete()
    await state.update_data({"now_product_id": now_product})
    os.remove(image_path)
    await callback.answer()


@router.callback_query(ProductMatchCallback.filter(F.action == "prev"))
async def product_button_previous_callback(callback: CallbackQuery, callback_data: ProductCallback, orm: ORM,
                                           state: FSMContext, keyboard: Keyboard, text_builder: TextBuilder):
    data = await state.get_data()
    now_product = data.get("now_product_id", 0)
    max_id_pm = data.get("max_id_pm")
    unique_products = data.get("unique_products")

    now_product -= 1
    if now_product < 0:
        now_product = max_id_pm

    products: list[Product] = await orm.product_match_repo.select_by_first_product_id(unique_products[now_product])

    text = f"Совпадение товаров {now_product + 1}/{len(unique_products)}\n"
    text += text_builder.build_product_match_text(products)

    markup = keyboard.product_match()

    image_path = merge_images_square([p.image_url for p in products])
    await callback.message.answer_photo(photo=FSInputFile(image_path), caption=text, parse_mode=ParseMode.HTML,
                                        reply_markup=markup)
    await callback.message.delete()
    await state.update_data({"now_product_id": now_product})
    os.remove(image_path)
    await callback.answer()
