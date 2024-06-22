import hashlib
import os

from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from database.database import ORM
from database.models import Product, ProductMatch
from methods.join_image import merge_images_horizontally
from tgbot.keyboards.callbacks import ProductMatchCallback, ProductCallback, HomeCallback
from tgbot.keyboards.keyboards import Keyboard

router = Router()


@router.callback_query(HomeCallback.filter(F.action == "matches"))
async def product_match_callback(callback: CallbackQuery, orm: ORM, state: FSMContext, keyboard: Keyboard):
    products_match: list[ProductMatch] = await orm.product_match_repo.select_all()

    if not products_match:
        await callback.answer("No products found.", show_alert=True)
        return

    product1: Product = await orm.product_repo.search_by_id(products_match[0].first_product_id)
    product2: Product = await orm.product_repo.search_by_id(products_match[0].second_product_id)

    text = f"Совпадение товаров 0/{len(products_match)}" \
           f"\n<b>{product1.name}</b>\nЦена: {product1.price}" \
           f"\n<a href='{product1.link}'>Ссылка на товар в {product1.category.site.name}</a>\n"
    text += f"↕️\n"
    text += f"<b>{product2.name}</b>\nЦена: {product2.price}" \
            f"\n<a href='{product2.link}'>Ссылка на товар в {product2.category.site.name}</a>"
    markup = keyboard.product_match()

    await state.update_data({"now_pm_id": 0, "max_id_pm": len(products_match) - 1})

    image_path = merge_images_horizontally(product1.image_url, product2.image_url,
                                           hashlib.md5((product1.image_url + product2.image_url).encode()).hexdigest())
    await callback.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(image_path),
                                  caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
    os.remove(image_path)
    await callback.answer()


# Обработка нажатий кнопок "next"
@router.callback_query(ProductMatchCallback.filter(F.action == "next"))
async def product_button_callback(callback: CallbackQuery, callback_data: ProductCallback, orm: ORM, state: FSMContext,
                                  keyboard: Keyboard):
    data = await state.get_data()
    now_pm = data.get("now_pm_id", 0)
    max_id_pm = data.get("max_id_pm")

    now_pm += 1
    if now_pm > max_id_pm:
        now_pm = 0

    products_match: list[ProductMatch] = await orm.product_match_repo.select_all()
    if not products_match:
        await callback.answer("No products found.", show_alert=True)
        return

    product1: Product = await orm.product_repo.search_by_id(products_match[now_pm].first_product_id)
    product2: Product = await orm.product_repo.search_by_id(products_match[now_pm].second_product_id)

    text = f"Совпадение товаров {now_pm}/{max_id_pm}" \
           f"\n<b>{product1.name}</b>\nЦена: {product1.price}" \
           f"\n<a href='{product1.link}'>Ссылка на товар в {product1.category.site.name}</a>\n"
    text += f"↕️\n"
    text += f"<b>{product2.name}</b>\nЦена: {product2.price}" \
            f"\n<a href='{product2.link}'>Ссылка на товар в {product2.category.site.name}</a>"

    markup = keyboard.product_match()
    await state.update_data({"now_pm_id": now_pm})

    image_path = merge_images_horizontally(product1.image_url, product2.image_url,
                                           hashlib.md5((product1.image_url + product2.image_url).encode()).hexdigest())
    await callback.message.answer_photo(photo=FSInputFile(image_path),
                                        caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
    await callback.message.delete()
    os.remove(image_path)
    await callback.answer()


@router.callback_query(ProductMatchCallback.filter(F.action == "prev"))
async def product_previous_button_callback(callback: CallbackQuery, callback_data: ProductCallback, orm: ORM,
                                           state: FSMContext, keyboard: Keyboard):
    data = await state.get_data()
    now_pm = data.get("now_pm_id", 0)
    max_id_pm = data.get("max_id_pm")

    now_pm -= 1
    if now_pm < 0:
        now_pm = max_id_pm

    products_match: list[ProductMatch] = await orm.product_match_repo.select_all()
    if not products_match:
        await callback.answer("No products found.", show_alert=True)
        return

    product1: Product = await orm.product_repo.search_by_id(products_match[now_pm].first_product_id)
    product2: Product = await orm.product_repo.search_by_id(products_match[now_pm].second_product_id)

    text = f"Совпадение товаров {now_pm}/{max_id_pm}" \
           f"\n<b>{product1.name}</b>\nЦена: {product1.price}" \
           f"\n<a href='{product1.link}'>Ссылка на товар в {product1.category.site.name}<a/>\n"
    text += f"↕️\n"
    text += f"<b>{product2.name}</b>\nЦена: {product2.price}" \
            f"\n<a href='{product2.link}'>Ссылка на товар в {product2.category.site.name}</a>"

    markup = keyboard.product_match()
    await state.update_data({"now_pm_id": now_pm})

    image_path = merge_images_horizontally(product1.image_url, product2.image_url,
                                           hashlib.md5((product1.image_url + product2.image_url).encode()).hexdigest())
    await callback.message.answer_photo(photo=FSInputFile(image_path),
                                        caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
    await callback.message.delete()
    os.remove(image_path)
    await callback.answer()
