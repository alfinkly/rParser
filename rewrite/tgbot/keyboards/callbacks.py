from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="category"):
    action: str
    id: int


class AuthCallback(CallbackData, prefix="auth"):
    action: int


class ProductCallback(CallbackData, prefix="product"):
    action: str


class ProductMatchCallback(CallbackData, prefix="pm"):
    action: str
