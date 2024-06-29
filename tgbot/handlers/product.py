from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineQuery, InlineKeyboardMarkup, InlineKeyboardButton, \
    InlineQueryResultArticle, InputTextMessageContent, input_media

from database.database import ORM
from database.models import GeneralCategory, Category, Product
from tgbot.handlers.states import ProductSearch
from tgbot.handlers.texts import generate_categories_text
from tgbot.keyboards.callbacks import CategoryCallback, ProductCallback

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tgbot.keyboards.product import categories_keyboard

router = Router()


@router.callback_query(CategoryCallback.filter(F.action == "g_category"))
async def process_category_selection(callback: CallbackQuery, callback_data: CategoryCallback, orm: ORM):
    g_category: GeneralCategory = await orm.general_category_repo.select_by_id(callback_data.id)
    text = generate_categories_text(g_category)
    markup = categories_keyboard(g_category)
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await callback.answer()


# async def show_products(message: Message, state: FSMContext, page: int = 0):
#     data = await state.get_data()
#     matched_products = data.get('matched_products', [])
#     page_cache = data.get('page_cache', {})
#     sent_products = data.get('sent_products', set())
#     last_message_ids = data.get('last_message_ids', [])
#
#     items_per_page = 5
#     total_pages = (len(matched_products) + items_per_page - 1) // items_per_page
#
#     if page in page_cache:
#         # Извлекаем товары из кэша страницы, если уже просматривали эту страницу
#         page_products = page_cache[page]
#     else:
#         # Выбираем товары для текущей страницы, если впервые на ней
#         start_index = page * items_per_page
#         end_index = start_index + items_per_page
#         page_products = []
#         for prod in matched_products[start_index:end_index]:
#             arbuz_id = prod[0]['_id'] if prod[0] else None
#             klever_id = prod[1]['_id'] if prod[1] else None
#             kaspi_id = prod[2]['_id'] if len(prod) > 2 and prod[2] else None
#
#             if not any(pid in sent_products for pid in [arbuz_id, klever_id, kaspi_id]):
#                 page_products.append(prod)
#                 if arbuz_id: sent_products.add(arbuz_id)
#                 if klever_id: sent_products.add(klever_id)
#                 if kaspi_id: sent_products.add(kaspi_id)
#
#         # Кэшируем товары текущей страницы
#         page_cache[page] = page_products
#
#     if not page_products:
#         await message.answer("Товары не найдены или вы достигли конца списка.")
#         return
#
#     for product_pair in page_products:
#         arbuz_product, klever_product, kaspi_product = product_pair if len(product_pair) > 2 else (
#             product_pair[0], product_pair[1], None)
#         arbuz_text, klever_text, kaspi_text, image_url = format_message(arbuz_product, klever_product,
#                                                                         kaspi_product)  # Обновите функцию format_message
#         text = arbuz_text + "\n" + klever_text + "\n" + kaspi_text  # Добавление текста для "Каспий"
#
#         markup = InlineKeyboardMarkup(row_width=2)
#         if arbuz_product and klever_product:
#             product_id = arbuz_product.get('_id', klever_product.get('_id', 'unknown'))
#             markup.add(
#                 InlineKeyboardButton("Соответствует", callback_data=f"match:{product_id}"),
#                 InlineKeyboardButton("Не соответствует", callback_data=f"nomatch:{product_id}")
#             )
#
#         try:
#             if image_url and image_url.startswith('http'):
#                 sent_message = await message.bot.send_photo(chat_id=message.chat.id, photo=image_url, caption=text,
#                                                             reply_markup=markup)
#             else:
#                 raise ValueError("Invalid image URL")
#         except Exception as e:
#             print(f"Ошибка при отправке изображения: {e}. Отправляю сообщение без изображения.")
#             sent_message = await message.answer(text, reply_markup=markup)
#
#         # Добавляем ID отправленного товара в список отправленных
#         if arbuz_product:
#             sent_products.add(arbuz_product['_id'])
#         if klever_product:
#             sent_products.add(klever_product['_id'])
#
#         last_message_ids.append(sent_message.message_id)
#
#     await state.update_data(page_cache=page_cache, sent_products=sent_products, last_message_ids=last_message_ids)
#
#     navigation_markup = InlineKeyboardMarkup(row_width=2)
#     if page > 0:
#         navigation_markup.insert(InlineKeyboardButton("⬅ Назад", callback_data=f"page:{page - 1}"))
#     if page + 1 < total_pages:
#         navigation_markup.insert(InlineKeyboardButton("Вперед ➡", callback_data=f"page:{page + 1}"))
#
#     navigation_markup.insert(InlineKeyboardButton("🔍 Инлайн-поиск", switch_inline_query_current_chat=""))
#
#     navigation_message = await message.answer("Перейдите на следующую страницу или используйте инлайн-поиск:",
#                                               reply_markup=navigation_markup)
#     last_message_ids.append(navigation_message.message_id)
#
#     # Обновляем состояние с новым списком ID отправленных сообщений и товаров
#     await state.update_data(page_cache=page_cache, sent_products=sent_products, last_message_ids=last_message_ids)


@router.inline_query()
async def find_product_query(inline_query: InlineQuery, orm: ORM, state: FSMContext):
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

    # Отправляем результаты пользователю
    await inline_query.answer(results=results, cache_time=3)


# @router.message(ProductSearch.search_ready)
# async def process_search_query(message: Message, state: FSMContext):
#     search_query = message.text.strip()
#     if not search_query:
#         await message.answer("Поисковый запрос не может быть пустым. Пожалуйста, введите название товара.")
#         return
#
#     if image_url:
#         await message.answer_photo(photo=image_url, caption=text)
#     else:
#         await message.answer(text)
#     # Завершаем сессию состояния
#     await state.finish()
#
#     # Показать пользователю кнопки для перехода по страницам, если есть более одного совпадения
#     if len(matched_products) > 1:
#         # Создаем клавиатуру для перехода по страницам
#         pagination_markup = InlineKeyboardMarkup()
#         pagination_markup.add(InlineKeyboardButton("➡️ Следующий товар", callback_data='next_product:1'))
#         await message.answer("Перейти к следующему товару:", reply_markup=pagination_markup)
#
#         # Сохраняем все совпадения и текущую страницу в состояние
#         await state.update_data(matched_products=matched_products, current_page=0)


@router.callback_query(CategoryCallback.filter(F.action == "category"))
async def category_button_callback(callback: CallbackQuery, callback_data: CategoryCallback,
                                   orm: ORM, state: FSMContext):
    products: list[Product] = await orm.product_repo.search_by_category(callback_data.id)

    if not products:
        await callback.answer("No products found.", show_alert=True)
        return

    product = products[0]  # Assuming products are not empty based on your initial approach
    photo_url = product.image_url
    title = product.name
    price = product.price
    text = f"<b>{title}</b>\nЦена: {price}\n<a href='{product.link}'>Ссылка на товар</a>"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подробнее", url=product.link)
        ], [
            InlineKeyboardButton(text="Вперед", callback_data=ProductCallback(action="next").pack())
        ]
    ])

    await state.update_data({"products": products, "now_product": 0})
    await callback.bot.send_photo(chat_id=callback.from_user.id, photo=photo_url, reply_markup=markup,
                                  caption=text, parse_mode=ParseMode.HTML)
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
