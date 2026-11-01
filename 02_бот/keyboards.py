"""Инлайн-клавиатуры. В callback_data только короткий код действия."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def menu_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Штаб", callback_data="status")],
        [InlineKeyboardButton(text="Построить", callback_data="build")],
        [InlineKeyboardButton(text="Следующая волна", callback_data="wave")],
        [
            InlineKeyboardButton(text="Рекорды", callback_data="top"),
            InlineKeyboardButton(text="Моя статистика", callback_data="stats"),
        ],
        [InlineKeyboardButton(text="Загрузить CSV", callback_data="upload")],
        [InlineKeyboardButton(text="Указать имя", callback_data="name")],
        [InlineKeyboardButton(text="Подписка на волны", callback_data="sub")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="Рассылка", callback_data="broadcast")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel")]]
    )
