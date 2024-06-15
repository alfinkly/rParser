button_states = {}  # Ключ: (user_id, product_id), Значение: 'match' или 'nomatch'


async def update_clicks(user_id, product_id, product_name, product_url, click_type, callback_query):
    # Обновляем состояние кнопок в хранилище
    button_states[(user_id, product_id)] = click_type

    collection = db['product_clicks']
    user_field = f"{click_type}_users"
    await collection.update_one(
        {"product_id": product_id},
        {"$set": {"product_name": product_name, "product_url": product_url},
         "$inc": {f"{click_type}_clicks": 1},
         "$addToSet": {user_field: user_id}},
        upsert=True
    )
    doc = await collection.find_one({"product_id": product_id})
    if doc:
        message = f"Товар '{product_name}' ({product_id}) был отмечен как {'соответствует' if click_type == 'match' else 'не соответствует'}. Текущее количество кликов: {doc[click_type + '_clicks']}."
        await bot.send_message(ADMIN_CHAT_ID, message)
        await callback_query.message.copy_to(ADMIN_CHAT_ID)

    # Обновляем сообщение с кнопками
    await refresh_message_buttons(callback_query, product_id)


async def refresh_message_buttons(callback_query: types.CallbackQuery, product_id: str):
    user_id = callback_query.from_user.id
    state = button_states.get((user_id, product_id), None)

    # Настраиваем текст кнопок в зависимости от состояния
    match_button_text = "✅ Соответствует" if state == "match" else "Соответствует"
    nomatch_button_text = "✅ Не соответствует" if state == "nomatch" else "Не соответствует"

    markup = InlineKeyboardMarkup(row_width=2)
    match_button = InlineKeyboardButton(match_button_text, callback_data=f"match:{product_id}")
    nomatch_button = InlineKeyboardButton(nomatch_button_text, callback_data=f"nomatch:{product_id}")
    markup.add(match_button, nomatch_button)

    # Обновляем сообщение с новой разметкой кнопок
    await callback_query.message.edit_reply_markup(reply_markup=markup)


@router.callback_query_handler(lambda c: c.data.startswith("match:"), state=ProductSearch.viewing)
async def handle_match(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = callback_query.data.split(':')[1]  # Извлекаем ID продукта
    # Здесь должен быть код для извлечения названия и ссылки продукта, пока используем заглушки
    product_name = "Product Name Placeholder"
    product_url = "http://example.com/placeholder"
    await update_clicks(callback_query.from_user.id, product_id, product_name, product_url, "match", callback_query)
    await callback_query.answer("Вы отметили товар как соответствующий.")


@router.callback_query_handler(lambda c: c.data.startswith('category:'), state='*')
async def process_category_selection(callback_query: types.CallbackQuery, state: FSMContext):
    # Парсим имя категории из callback_data
    category = callback_query.data.split(':')[1]
    await callback_query.answer()

    # Ищем товары в Арбузе
    arbuz_products = await arbuz_collection.find({'category': category}).to_list(None)

    # Используем category_mapping для поиска соответствующих категорий в Клевере и Каспий
    klever_categories = category_mapping.get(category, [])
    klever_products = []
    kaspi_products = []  # Инициализация списка товаров из Каспий
    for klever_category in klever_categories:
        klever_products.extend(await klever_collection.find({'category': klever_category}).to_list(None))
        # Допустим, что категории для Каспий те же, что и для Клевер. Если это не так, необходимо настроить соответствующее отображение
        kaspi_products.extend(await kaspi_collection.find({'category': klever_category}).to_list(None))

    # Проверяем, есть ли уже сравнения для данной категории в кэше
    if category not in matched_products_cache:
        # Теперь передаем все три списка товаров в функцию
        matched_products = await find_matching_products(arbuz_products, klever_products, kaspi_products,
                                                        category_mapping)
        matched_products_cache[category] = matched_products

    # Сохраняем сравненные товары в состояние
    await state.update_data(matched_products=matched_products_cache[category])

    if matched_products_cache[category]:
        await show_products(callback_query.message, state)
    else:
        await callback_query.message.edit_text("Соответствующие товары не найдены.")


@router.callback_query_handler(lambda c: c.data.startswith("nomatch:"), state=ProductSearch.viewing)
async def handle_nomatch(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = callback_query.data.split(':')[1]  # Извлекаем ID продукта
    user_id = callback_query.from_user.id  # ID пользователя, который нажал кнопку

    # Извлечение информации о продукте (здесь используется заглушка)
    product_name = "Product Name Placeholder"
    product_url = "http://example.com/placeholder"

    # Обновляем информацию о кликах
    await update_clicks(callback_query.from_user.id, product_id, product_name, product_url, "nomatch", callback_query)

    # Извлекаем номер телефона и имя пользователя из базы данных
    user_contact = await db['user_contacts'].find_one({'user_id': user_id})
    if user_contact:
        phone_number = user_contact.get('phone_number', 'Номер не предоставлен')
        first_name = user_contact.get('first_name', 'Имя не предоставлено')
        last_name = user_contact.get('last_name', '')

        # Составляем сообщение администратору
        admin_message = (
            f"Пользователь: {first_name} {last_name}\n"
            f"ID: {user_id}\n"
            f"Телефон: {phone_number}\n"
            f"Отметил товар как 'Не соответствует':\n"
            f"{product_name}\n"
            f"{product_url}"
        )
        await bot.send_message(ADMIN_CHAT_ID, admin_message)
    else:
        await bot.send_message(ADMIN_CHAT_ID, f"Пользователь с ID {user_id} не найден в базе данных.")

    await callback_query.answer("Вы отметили товар как не соответствующий.")


page_storage = {}


# Обработчик пагинации
@router.callback_query_handler(lambda c: c.data.startswith("page:"), state='*')
async def navigate_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split(':')[1])

    # Получаем и обновляем данные пользователя
    data = await state.get_data()
    last_message_ids = data.get('last_message_ids', [])
    # Здесь добавьте логику для обновления данных пользователя, если необходимо

    # Удаляем предыдущие сообщения
    for message_id in last_message_ids:
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=message_id)
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение с ID {message_id}: {e}")

    # Очищаем список ID в состоянии
    await state.update_data(last_message_ids=[])

    # Переходим к отображению продуктов на новой странице
    await show_products(callback_query.message, state, page)
    await callback_query.answer()


def format_message(arbuz_product=None, klever_product=None, kaspi_product=None, base_url_arbuz="https://arbuz.kz",
                   base_url_klever="https://klever.kz", base_url_kaspi="https://kaspi.kz"):
    arbuz_text = ""
    klever_text = ""
    kaspi_text = ""  # Текст для "Каспий"
    image_url = None

    if arbuz_product:
        # Формируем информацию о продукте из Арбуза
        arbuz_text = (
            f"Арбуз:\n"
            f"Название: {arbuz_product.get('name', 'Название отсутствует')}\n"
            f"Цена: {arbuz_product.get('price', 'Цена отсутствует')}\n"
            f"Категория: {arbuz_product.get('category', 'Категория отсутствует')}\n"
            f"Актуально на: {arbuz_product.get('parsed_time', 'Время не указано')}\n"
            f"Ссылка: {base_url_arbuz + arbuz_product.get('link', '')}\n"
        )
        image_url = arbuz_product.get('image_url', None)
    else:
        arbuz_text = "Соответствий в Арбузе не найдено.\n"

    if klever_product:
        # Формируем информацию о продукте из Клевера
        klever_text = (
            f"Клевер:\n"
            f"Название: {klever_product.get('name', 'Название отсутствует')}\n"
            f"Цена: {klever_product.get('price', 'Цена отсутствует')}\n"
            f"Категория: {klever_product.get('category', 'Категория отсутствует')}\n"
            f"Актуально на: {klever_product.get('parsed_time', 'Время не указано')}\n"
            f"Ссылка: {klever_product.get('link', '')}\n"
        )
        # Изображение товара из Клевера используется, если нет изображения из Арбуза
        image_url = image_url or klever_product.get('image_url', None)
    else:
        klever_text = "Соответствий в Клевере не найдено.\n"

    if kaspi_product:
        # Формируем информацию о продукте из Каспий
        kaspi_text = (
            f"Каспий:\n"
            f"Название: {kaspi_product.get('name', 'Название отсутствует')}\n"
            f"Цена: {kaspi_product.get('price', 'Цена отсутствует')}\n"
            f"Категория: {kaspi_product.get('category', 'Категория отсутствует')}\n"
            f"Актуально на: {kaspi_product.get('parsed_time', 'Время не указано')}\n"
            f"Ссылка: {kaspi_product.get('product_url', '')}\n"
        )
        # Изображение товара из Каспий используется, если нет изображения из других магазинов
        image_url = image_url or kaspi_product.get('image_url', None)
    else:
        kaspi_text = "Соответствий в Каспии не найдено.\n"

    return arbuz_text, klever_text, kaspi_text, image_url


@router.callback_query_handler(lambda c: c.data.startswith('page:'), state='*')
async def handle_page_change(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем номер страницы из callback данных
    page_number = int(callback_query.data.split(':')[1])

    # Попытка удалить предыдущее сообщение бота
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except Exception as e:
        logger.error(f"Не удалось удалить сообщение: {e}")

    # Показываем продукты на новой странице
    await show_products(callback_query.message, state, page=page_number)


@router.message_handler(state=ProductSearch.waiting_for_search_query)
async def process_search_query(message: types.Message, state: FSMContext):
    search_query = message.text.strip()
    if not search_query:
        await message.answer("Поисковый запрос не может быть пустым. Пожалуйста, введите название товара.")
        return

    # Выполнение поиска в коллекциях Арбуз и Клевер
    arbuz_products = await arbuz_collection.find({'$text': {'$search': search_query}}).to_list(length=100)
    klever_products = await klever_collection.find({'$text': {'$search': search_query}}).to_list(length=100)
    kaspi_products = await kaspi_collection.find({'$text': {'$search': search_query}}).to_list(length=100)

    # Поиск совпадений между двумя коллекциями
    matched_products = await find_matching_products(arbuz_products, klever_products, kaspi_products)

    # Проверяем, есть ли совпадающие товары
    if not matched_products:
        await message.answer("Товары по запросу не найдены.")
        await state.finish()
        return

    # Выводим информацию о первом совпадении
    # (Для упрощения предполагаем, что совпадения уже отсортированы по релевантности)
    arbuz_product, klever_product, kaspi_product = matched_products[0]

    # Обновляем вызов format_message, чтобы он теперь принимал три продукта
    arbuz_text, klever_text, kaspi_text, image_url = format_message(arbuz_product, klever_product, kaspi_product)

    # Формируем текст сообщения, включающий информацию из всех трех источников
    text = f"{arbuz_text}\n{klever_text}\n{kaspi_text}"

    # Отправляем результаты пользователю
    if image_url:
        await message.answer_photo(photo=image_url, caption=text)
    else:
        await message.answer(text)
    # Завершаем сессию состояния
    await state.finish()

    # Показать пользователю кнопки для перехода по страницам, если есть более одного совпадения
    if len(matched_products) > 1:
        # Создаем клавиатуру для перехода по страницам
        pagination_markup = InlineKeyboardMarkup()
        pagination_markup.add(InlineKeyboardButton("➡️ Следующий товар", callback_data='next_product:1'))
        await message.answer("Перейти к следующему товару:", reply_markup=pagination_markup)

        # Сохраняем все совпадения и текущую страницу в состояние
        await state.update_data(matched_products=matched_products, current_page=0)