from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder

from database.database import ORM
from database.models import Product, ProductMatch
from tgbot.keyboards.callbacks import ProductMatchCallback, ProductCallback

router = Router()


@router.callback_query(ProductMatchCallback.filter())
async def product_match_callback(callback: CallbackQuery, callback_data: ProductMatchCallback,
                                 orm: ORM, state: FSMContext):
    products_match: list[ProductMatch] = await orm.product_match_repo.select_all()

    if not products_match:
        await callback.answer("No products found.", show_alert=True)
        return

    product1 = products_match[0].first_product_id
    product2 = products_match[0].second_product_id
    # photo_url = product.image_url
    # title = product.name
    # price = product.price
    text = f"<b>{product1.title}</b>\nЦена: {product1.price}\n<a href='{product1.link}'>Ссылка на товар</a>\n"
    text += f"↕️\n"
    text += f"<b>{product2.title}</b>\nЦена: {product2.price}\n<a href='{product2.link}'>Ссылка на товар</a>"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{product1.title}", url=product1.link)
        ], [
            InlineKeyboardButton(text=f"{product2.title}", url=product2.link)
        ], [
            InlineKeyboardButton(text="Назад", callback_data=ProductCallback(action="prev").pack()),
            InlineKeyboardButton(text="Вперед", callback_data=ProductCallback(action="next").pack())
        ]
    ])

    await state.update_data({"products_match": products_match, "now_product_match": 0})
    media = MediaGroupBuilder(caption=text)
    media.add(type="photo", media=product1.photo_url, parse_mode=ParseMode.HTML)
    media.add(type="photo", media=product2.photo_url, parse_mode=ParseMode.HTML)
    await callback.bot.send_media_group(chat_id=callback.from_user.id, media=media.build())
    await callback.answer()


@router.callback_query(ProductCallback.filter(F.action == "next"))
async def product_button_callback(callback: CallbackQuery, callback_data: ProductCallback,
                                  orm: ORM, state: FSMContext):
    data = await state.get_data()
    products = data.get("products", [])
    now_product = data.get("now_product", 0)

    now_product += 1

    if now_product >= len(products):
        await callback.answer("No more products.", show_alert=True)
        return

    product = products[now_product]

    photo_url = product.image_url
    title = product.name
    price = product.price
    text = f"<b>{title}</b>\nЦена: {price}\n<a href='{product.link}'>Ссылка на товар</a>"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подробнее", url=product.link)
        ], []
    ])

    if now_product > 0:
        markup.inline_keyboard[1].append(
            InlineKeyboardButton(text="Назад", callback_data=ProductCallback(action="prev").pack())
        )

    if now_product < len(products) - 1:
        markup.inline_keyboard[1].append(
            InlineKeyboardButton(text="Вперед", callback_data=ProductCallback(action="next").pack())
        )

    await state.update_data({"now_product": now_product})
    media = types.InputMediaPhoto(media=photo_url, caption=text, parse_mode=ParseMode.HTML)
    await callback.message.edit_media(media=media, reply_markup=markup)
    await callback.answer()


@router.callback_query(ProductCallback.filter(F.action == "prev"))
async def product_button_callback(callback: CallbackQuery, callback_data: ProductCallback,
                                  orm: ORM, state: FSMContext):
    data = await state.get_data()
    products = data.get("products", [])
    now_product = data.get("now_product", 0)

    now_product -= 1

    if now_product < 0:
        await callback.answer("No previous products.", show_alert=True)
        return

    product = products[now_product]

    photo_url = product.image_url
    title = product.name
    price = product.price
    text = f"<b>{title}</b>\nЦена: {price}\n<a href='{product.link}'>Ссылка на товар</a>"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подробнее", url=product.link)
        ], []
    ])

    if now_product > 0:
        markup.inline_keyboard[1].append(
            InlineKeyboardButton(text="Назад", callback_data=ProductCallback(action="prev").pack())
        )

    if now_product < len(products) - 1:
        markup.inline_keyboard[1].append(
            InlineKeyboardButton(text="Вперед", callback_data=ProductCallback(action="next").pack())
        )

    await state.update_data({"now_product": now_product})
    media = types.InputMediaPhoto(media=photo_url, caption=text, parse_mode=ParseMode.HTML)
    await callback.message.edit_media(media=media, reply_markup=markup)
    await callback.answer()
