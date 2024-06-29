import os

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from database.database import ORM
from database.models import Product, GeneralProduct
from methods.join_image import merge_images_square
from tgbot.keyboards.callbacks import ProductMatchCallback, ProductCallback, HomeCallback
from tgbot.middlewares.keyboards import Keyboard
from tgbot.middlewares.texts import Text

router = Router()


@router.callback_query(HomeCallback.filter(F.action == "matches"))
async def general_product_callback(callback: CallbackQuery, orm: ORM, state: FSMContext, keyboard: Keyboard,
                                   texts: Text):
    products_match: list[GeneralProduct] = await orm.general_product_repo.select_all()

    if not products_match:
        await callback.answer("No products found.", show_alert=True)
        return

    unique_products = await orm.general_product_repo.select_unique_first_product_ids()
    products: list[Product] = await orm.general_product_repo.select_by_first_product_id(unique_products[0])
    text = f"Совпадение товаров 1/{len(unique_products)}\n"
    text += texts.build_general_product_text(products)
    markup = keyboard.general_product()

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
                                  keyboard: Keyboard, texts: Text):
    data = await state.get_data()
    now_product = data.get("now_product_id", 0)
    max_id_pm = data.get("max_id_pm")
    unique_products = data.get("unique_products")

    now_product += 1
    if now_product > max_id_pm:
        now_product = 0

    products: list[Product] = await orm.general_product_repo.select_by_first_product_id(unique_products[now_product])

    text = f"Совпадение товаров {now_product + 1}/{len(unique_products)}\n"
    text += texts.build_general_product_text(products)

    markup = keyboard.general_product()

    image_path = merge_images_square([p.image_url for p in products])
    await callback.message.answer_photo(photo=FSInputFile(image_path), caption=text, parse_mode=ParseMode.HTML,
                                        reply_markup=markup)
    await callback.message.delete()
    await state.update_data({"now_product_id": now_product})
    os.remove(image_path)
    await callback.answer()


@router.callback_query(ProductMatchCallback.filter(F.action == "prev"))
async def product_button_previous_callback(callback: CallbackQuery, callback_data: ProductCallback, orm: ORM,
                                           state: FSMContext, keyboard: Keyboard, texts: Text):
    data = await state.get_data()
    now_product = data.get("now_product_id", 0)
    max_id_pm = data.get("max_id_pm")
    unique_products = data.get("unique_products")

    now_product -= 1
    if now_product < 0:
        now_product = max_id_pm

    products: list[Product] = await orm.general_product_repo.select_by_first_product_id(unique_products[now_product])

    text = f"Совпадение товаров {now_product + 1}/{len(unique_products)}\n"
    text += texts.build_general_product_text(products)

    markup = keyboard.general_product()

    image_path = merge_images_square([p.image_url for p in products])
    await callback.message.answer_photo(photo=FSInputFile(image_path), caption=text, parse_mode=ParseMode.HTML,
                                        reply_markup=markup)
    await callback.message.delete()
    await state.update_data({"now_product_id": now_product})
    os.remove(image_path)
    await callback.answer()
