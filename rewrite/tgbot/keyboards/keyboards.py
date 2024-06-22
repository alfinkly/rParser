from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.keyboards.callbacks import HomeCallback, ProductMatchCallback


class Keyboard:
    @staticmethod
    def home():
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Все товары", callback_data=HomeCallback(action="products").pack()),
            InlineKeyboardButton(text="Соответствия по товарам", callback_data=HomeCallback(action="matches").pack()),
        ]])
        return markup

    @staticmethod
    def product_match():
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Назад", callback_data=ProductMatchCallback(action="prev").pack()),
                InlineKeyboardButton(text="Вперед", callback_data=ProductMatchCallback(action="next").pack())
            ]
        ])
        return markup
