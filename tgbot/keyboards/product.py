from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Category
from tgbot.keyboards.callbacks import CategoryCallback


def categories_keyboard(g_category):
    markup = InlineKeyboardMarkup(inline_keyboard=[[]])
    for c in g_category.categories:
        c: Category
        button = InlineKeyboardButton(text=c.name, callback_data=CategoryCallback(action="category", id=c.id).pack())
        markup.inline_keyboard[0].append(button)
    return markup