from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from database.models import GeneralCategory, Product, GeneralProduct
from tgbot.keyboards.callbacks import HomeCallback, ProductMatchCallback, CategoryCallback, ProductCallback


class Keyboard:
    @staticmethod
    def home():
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Все категории", callback_data=HomeCallback(action="category").pack()),
            InlineKeyboardButton(text="Найти товар", switch_inline_query_current_chat="")
        ]])
        return markup

    @staticmethod
    def general_product():
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Назад", callback_data=ProductMatchCallback(action="prev").pack()),
                InlineKeyboardButton(text="Вперед", callback_data=ProductMatchCallback(action="next").pack())
            ]
        ])
        return markup

    @staticmethod
    def send_phone():
        return ReplyKeyboardMarkup(resize_keyboard=True,
                                   one_time_keyboard=True,
                                   keyboard=[[
                                       KeyboardButton(text='Поделиться номером телефона', request_contact=True)
                                   ]])

    @staticmethod
    def categories(categories: list[GeneralCategory]):
        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for c in categories:
            markup.inline_keyboard.append([
                InlineKeyboardButton(text=c.name, callback_data=CategoryCallback(action="go", id=c.id).pack())
            ])
        return markup

    @staticmethod
    def product_match(product_id, is_favorite: bool):
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Предыдущий",
                                     callback_data=ProductCallback(action="prev", id=product_id).pack()),
                InlineKeyboardButton(text="Следующий ➡️",
                                     callback_data=ProductCallback(action="next", id=product_id).pack())
            ],
            [
                InlineKeyboardButton(text="Тут ошибка 🚫",
                                     callback_data=ProductCallback(action="not_match", id=product_id).pack())
            ],
        ])
        if is_favorite:
            markup.inline_keyboard.append([
                InlineKeyboardButton(text="Убрать из избранных ❤️",
                                     callback_data=ProductCallback(action="favorite", id=product_id).pack())
            ])
        else:
            markup.inline_keyboard.append([
                InlineKeyboardButton(text="Добавить в избранные 💔",
                                     callback_data=ProductCallback(action="favorite", id=product_id).pack())
            ])
        markup.inline_keyboard.append([
                InlineKeyboardButton(text="Избранные 💟",
                                     callback_data=ProductCallback(action="favorites", id=product_id).pack())
            ],)
        return markup