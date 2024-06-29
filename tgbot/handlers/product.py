import os

from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineQuery, InlineKeyboardMarkup, InlineKeyboardButton, \
    InlineQueryResultArticle, InputTextMessageContent, input_media, FSInputFile

from database.database import ORM
from database.models import GeneralCategory, Category, Product, GeneralProduct
from methods.join_image import merge_images_square
from tgbot.handlers.states import ProductSearch
from tgbot.handlers.texts import generate_categories_text
from tgbot.keyboards.callbacks import CategoryCallback, ProductCallback

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tgbot.keyboards.product import categories_keyboard
from tgbot.middlewares.keyboards import Keyboard
from tgbot.middlewares.texts import Text

router = Router()


@router.callback_query(CategoryCallback.filter(F.action == "g_category"))
async def process_category_selection(callback: CallbackQuery,
                                     callback_data: CategoryCallback,
                                     orm: ORM):
    g_category: GeneralCategory = await orm.general_category_repo.select_by_id(callback_data.id)
    text = generate_categories_text(g_category)
    markup = categories_keyboard(g_category)
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await callback.answer()


@router.inline_query()
async def find_product_query(inline_query: InlineQuery,
                             orm: ORM,
                             state: FSMContext):
    query = inline_query.query.strip()
    results = []
    if query:
        products: list[Product] = await orm.product_repo.search_by_name(query)
        for product in products:
            photo_url = product.image_url
            title = product.name
            price = product.price
            markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подробнее", url=product.link)]])
            results.append(
                InlineQueryResultArticle(
                    id=str(product.id),
                    title=title,
                    input_message_content=InputTextMessageContent(
                        message_text=f"<b>{title}</b>\nЦена: {price}\n<a href='{product.link}'>Ссылка на товар</a>",
                        parse_mode=ParseMode.HTML
                    ),
                    reply_markup=markup,
                    thumb_url=photo_url,
                    description=f"Цена: {price}"
                )
            )
    await state.update_data({"results": results})
    results = results[:20]
    await inline_query.answer(results=results, cache_time=3)


@router.callback_query(ProductCallback.filter(F.action == "next"))
async def next_product(callback: CallbackQuery,
                       state: FSMContext,
                       orm: ORM,
                       keyboard: Keyboard,
                       texts: Text):
    data = await state.get_data()
    category_products = data.get("category_products", [])
    current_index = data.get("current_index", 0)
    favorites = data.get("favorites", [])
    new_index = (current_index + 1) % len(category_products)
    first_product = category_products[new_index]
    match_products: list[Product] = await orm.general_product_repo.select_by_first_product_id(
        first_product.first_product_id)
    if category_products[new_index] in favorites:
        markup = keyboard.product_match(first_product.id, is_favorite=True)
    else:
        markup = keyboard.product_match(first_product.id, is_favorite=False)

    await state.update_data(current_index=new_index)
    text = texts.build_general_product_text(match_products)
    image_path = merge_images_square([p.image_url for p in match_products])
    await callback.message.answer_photo(photo=FSInputFile(image_path),
                                        caption=text,
                                        reply_markup=markup,
                                        parse_mode=ParseMode.HTML)
    await callback.message.delete()
    os.remove(image_path)


@router.callback_query(ProductCallback.filter(F.action == "prev"))
async def prev_product(callback: CallbackQuery,
                       state: FSMContext,
                       orm: ORM,
                       keyboard: Keyboard,
                       texts: Text):
    data = await state.get_data()
    category_products = data.get("category_products", [])
    current_index = data.get("current_index", 0)
    favorites = data.get("favorites", [])
    new_index = (current_index - 1 + len(category_products)) % len(category_products)
    product = category_products[new_index]
    match_products: list[Product] = await orm.general_product_repo.select_by_first_product_id(product.first_product_id)

    await state.update_data(current_index=new_index)
    if category_products[new_index] in favorites:
        markup = keyboard.product_match(product.id, is_favorite=True)
    else:
        markup = keyboard.product_match(product.id, is_favorite=False)
    text = texts.build_general_product_text(match_products)
    image_path = merge_images_square([p.image_url for p in match_products])
    await callback.message.answer_photo(photo=FSInputFile(image_path),
                                        caption=text,
                                        reply_markup=markup,
                                        parse_mode=ParseMode.HTML)
    await callback.message.delete()
    os.remove(image_path)


@router.callback_query(ProductCallback.filter(F.action == "favorite"))
async def add_to_cart(callback: CallbackQuery,
                      callback_data: ProductCallback,
                      keyboard: Keyboard,
                      texts: Text,
                      orm: ORM,
                      state: FSMContext):
    data = await state.get_data()
    category_products = data.get("category_products", [])
    current_index = data.get("current_index", 0)
    favorites = data.get("favorites", [])
    if category_products[current_index] in favorites:
        favorites.remove(category_products[current_index])
        await callback.message.edit_reply_markup(reply_markup=keyboard.product_match(current_index, is_favorite=False))
    else:
        favorites.append(category_products[current_index])
        await callback.message.edit_reply_markup(reply_markup=keyboard.product_match(current_index, is_favorite=True))
    await state.update_data({"favorites": favorites})

    await callback.answer()


@router.callback_query(ProductCallback.filter(F.action == "favorites"))
async def add_to_cart(callback: CallbackQuery,
                      callback_data: ProductCallback,
                      keyboard: Keyboard,
                      texts: Text,
                      orm: ORM,
                      state: FSMContext):
    data = await state.get_data()
    category_products = data.get("category_products", [])
    current_index = data.get("current_index", 0)
    favorites = data.get("favorites", [])
    if category_products[current_index] in favorites:
        favorites.remove(category_products[current_index])
        await callback.message.edit_reply_markup(reply_markup=keyboard.product_match(current_index, is_favorite=False))
    else:
        favorites.append(category_products[current_index])
        await callback.message.edit_reply_markup(reply_markup=keyboard.product_match(current_index, is_favorite=True))
    await state.update_data({"favorites": favorites})

    await callback.answer()
