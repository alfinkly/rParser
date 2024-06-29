from aiogram.fsm.state import StatesGroup, State


class ProductSearch(StatesGroup):
    choosing_category = State()
    search_ready = State()


class AuthState(StatesGroup):
    wait_contact = State()