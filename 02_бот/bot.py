"""Бот «Штаб обороны». Сервис к игре: рекорды, лог и приказы на постройку.

Токен берётся из 02_бот/.env. Поле Pygame в чат не копируется.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramServerError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, ErrorEvent, Message

import analytics
import keyboards
import simulation
from config import ADMIN_IDS, BOT_LOG_PATH, BOT_TOKEN, WAVE_INTERVAL_SECONDS
from session import all_sessions, load_session, save_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(BOT_LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("hq")


class BotState(StatesGroup):
    MENU = State()
    UPLOAD = State()
    WAIT_NAME = State()
    BUILD = State()
    BROADCAST = State()


bot = None
dp = Dispatcher(storage=MemoryStorage())


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def show_screen(chat_id: int, user_id: int, text: str, keyboard, state_name: str | None = None) -> None:
    """Правит одно сообщение-экран. Новое сообщение уходит, только если править нечего."""
    session = load_session(user_id)
    if state_name is not None:
        session["state"] = state_name
        save_session(user_id, session)
    screen_id = session.get("screen_message_id")
    screen_chat = session.get("screen_chat_id")
    if screen_id and screen_chat == chat_id:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=screen_id,
                reply_markup=keyboard,
            )
            return
        except TelegramBadRequest as error:
            if "message is not modified" in str(error):
                return
            logger.info("Экран %s недоступен (%s), отправляем новый", screen_id, error)
        except (TelegramNetworkError, TelegramServerError) as error:
            logger.info("Сеть при правке экрана: %s", error)
    try:
        message = await bot.send_message(chat_id, text, reply_markup=keyboard)
    except (TelegramNetworkError, TelegramServerError):
        message = await bot.send_message(chat_id, text, reply_markup=keyboard)
    session["screen_message_id"] = message.message_id
    session["screen_chat_id"] = chat_id
    save_session(user_id, session)


def _menu_text(user_id: int) -> str:
    session = load_session(user_id)
    name = session.get("name") or "не указано"
    sub = "включена" if session.get("subscribed") else "выключена"
    return (
        "Штаб обороны\n"
        f"Имя: {name}\n"
        f"Подписка на волны: {sub}\n"
        f"Ваш id: {user_id}\n\n"
        "Приказ на постройку: /build лазер 3 5\n"
        "Типы: лазер, пулемёт, мортира."
    )


async def _safe_answer(callback: CallbackQuery, text: str = "") -> None:
    try:
        await callback.answer(text)
    except TelegramBadRequest:
        return


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    await state.set_state(BotState.MENU)
    user_id = message.from_user.id
    logger.info("Команда /start от %s", user_id)
    await show_screen(
        message.chat.id,
        user_id,
        _menu_text(user_id),
        keyboards.menu_keyboard(_is_admin(user_id)),
        "MENU",
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if message.from_user is None:
        return
    text = (
        "Бот читает scores.csv и log_defense.txt из папки игры и принимает приказы штаба.\n"
        "/build тип столбец строка — поставить башню, если хватает золота.\n"
        "Кнопка «Следующая волна» считает бой по текущим башням.\n"
        "Подписчикам то же уведомление уходит раз в час, пока бот запущен.\n"
        "Кнопка «Загрузить CSV» принимает выгрузку результатов."
    )
    await show_screen(
        message.chat.id,
        message.from_user.id,
        text,
        keyboards.menu_keyboard(_is_admin(message.from_user.id)),
        "MENU",
    )


@dp.message(Command("build"))
async def cmd_build(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    await state.set_state(BotState.MENU)
    user_id = message.from_user.id
    session = load_session(user_id)
    result = _apply_build(session, message.text)
    save_session(user_id, session)
    logger.info("Приказ /build от %s: %s", user_id, result)
    await show_screen(
        message.chat.id,
        user_id,
        result,
        keyboards.menu_keyboard(_is_admin(user_id)),
        "MENU",
    )


def _apply_build(session: dict, text: str) -> str:
    payload = text.strip()
    if payload.startswith("/build"):
        payload = payload[len("/build"):].strip()
    parts = payload.split()
    if len(parts) != 3:
        return "Формат приказа: /build лазер 3 5"
    tower_type, col_text, row_text = parts
    try:
        col = int(col_text)
        row = int(row_text)
    except ValueError:
        return "Столбец и строка должны быть целыми числами."
    return simulation.place_tower(session, tower_type, col, row)


@dp.callback_query(F.data == "cancel")
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.MENU)
    await _safe_answer(callback, "Отменено")
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        _menu_text(callback.from_user.id),
        keyboards.menu_keyboard(_is_admin(callback.from_user.id)),
        "MENU",
    )


@dp.callback_query(F.data == "status")
async def on_status(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.MENU)
    session = load_session(callback.from_user.id)
    text = simulation.status_text(session) + "\n\n" + analytics.read_defense_log()
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        text,
        keyboards.menu_keyboard(_is_admin(callback.from_user.id)),
        "MENU",
    )


@dp.callback_query(F.data == "build")
async def on_build(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.BUILD)
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        "Напишите приказ: лазер 3 5\nТипы: лазер, пулемёт, мортира.",
        keyboards.cancel_keyboard(),
        "BUILD",
    )


@dp.message(StateFilter(BotState.BUILD), F.text)
async def on_build_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    user_id = message.from_user.id
    session = load_session(user_id)
    result = _apply_build(session, message.text)
    save_session(user_id, session)
    await state.set_state(BotState.MENU)
    logger.info("Приказ из режима постройки от %s: %s", user_id, result)
    await show_screen(
        message.chat.id,
        user_id,
        result,
        keyboards.menu_keyboard(_is_admin(user_id)),
        "MENU",
    )


@dp.callback_query(F.data == "wave")
async def on_wave(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.MENU)
    user_id = callback.from_user.id
    session = load_session(user_id)
    report = simulation.resolve_next_wave(session)
    save_session(user_id, session)
    logger.info("Волна по кнопке для %s", user_id)
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        user_id,
        report,
        keyboards.menu_keyboard(_is_admin(user_id)),
        "MENU",
    )


@dp.callback_query(F.data == "top")
async def on_top(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.MENU)
    records, errors = analytics.read_scores()
    text = analytics.format_leaderboard(records)
    if errors and not records:
        text = "Таблица пуста.\n" + "\n".join(errors[:5])
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        text,
        keyboards.menu_keyboard(_is_admin(callback.from_user.id)),
        "MENU",
    )


@dp.callback_query(F.data == "stats")
async def on_stats(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.MENU)
    session = load_session(callback.from_user.id)
    name = session.get("name")
    if not name:
        text = "Сначала укажите имя кнопкой «Указать имя»."
    else:
        records, _errors = analytics.read_scores()
        text = analytics.personal_stats(records, name) + "\n\n" + "\n".join(
            analytics.achievements(records, name)
        )
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        text,
        keyboards.menu_keyboard(_is_admin(callback.from_user.id)),
        "MENU",
    )


@dp.callback_query(F.data == "upload")
async def on_upload(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.UPLOAD)
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        "Пришлите CSV с колонками Имя, Волна, Статус, Время.",
        keyboards.cancel_keyboard(),
        "UPLOAD",
    )


@dp.message(StateFilter(BotState.UPLOAD), F.document)
async def on_document(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.document is None:
        return
    document = message.document
    if document.file_size and document.file_size > 1_000_000:
        await message.answer("Файл больше 1 МБ, он не принят.")
        return
    name = (document.file_name or "").lower()
    if not name.endswith(".csv") and document.mime_type not in {"text/csv", "text/plain"}:
        await message.answer("Нужен файл CSV.")
        return
    buffer = await bot.download(document)
    raw = buffer.read() if hasattr(buffer, "read") else bytes(buffer)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        await message.answer("Файл не в кодировке UTF-8.")
        return
    records, errors = analytics.parse_scores_text(text)
    added = analytics.append_records(records) if records else 0
    logger.info("Загрузка CSV от %s: добавлено %s, ошибок %s", message.from_user.id, added, len(errors))
    await state.set_state(BotState.MENU)
    report = f"Добавлено записей: {added}\nОтклонено строк: {len(errors)}"
    if errors:
        report += "\n" + "\n".join(errors[:8])
    await show_screen(
        message.chat.id,
        message.from_user.id,
        report,
        keyboards.menu_keyboard(_is_admin(message.from_user.id)),
        "MENU",
    )
    if added:
        await _notify_subscribers(message.from_user.id, f"В таблицу добавлено записей: {added}")


@dp.message(StateFilter(BotState.UPLOAD))
async def on_upload_other(message: Message) -> None:
    await message.answer("Жду CSV-файл или нажмите «Отмена».")


@dp.callback_query(F.data == "name")
async def on_name(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await state.set_state(BotState.WAIT_NAME)
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        "Напишите имя для таблицы результатов. До 18 символов.",
        keyboards.cancel_keyboard(),
        "WAIT_NAME",
    )


@dp.message(StateFilter(BotState.WAIT_NAME), F.text)
async def on_name_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    name = " ".join(message.text.split())[:18]
    if not name or name.startswith("/"):
        await message.answer("Имя не принято.")
        return
    user_id = message.from_user.id
    session = load_session(user_id)
    session["name"] = name
    save_session(user_id, session)
    await state.set_state(BotState.MENU)
    logger.info("Имя пользователя %s сохранено", user_id)
    await show_screen(
        message.chat.id,
        user_id,
        f"Имя сохранено: {name}",
        keyboards.menu_keyboard(_is_admin(user_id)),
        "MENU",
    )


@dp.callback_query(F.data == "sub")
async def on_sub(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        return
    user_id = callback.from_user.id
    session = load_session(user_id)
    session["subscribed"] = not session.get("subscribed", False)
    save_session(user_id, session)
    logger.info("Подписка %s: %s", user_id, session["subscribed"])
    await _safe_answer(callback, "Подписка обновлена")
    await show_screen(
        callback.message.chat.id,
        user_id,
        _menu_text(user_id),
        keyboards.menu_keyboard(_is_admin(user_id)),
        "MENU",
    )


@dp.callback_query(F.data == "broadcast")
async def on_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return
    if not _is_admin(callback.from_user.id):
        await _safe_answer(callback, "Недостаточно прав")
        return
    await state.set_state(BotState.BROADCAST)
    await _safe_answer(callback)
    await show_screen(
        callback.message.chat.id,
        callback.from_user.id,
        "Напишите текст рассылки подписчикам.",
        keyboards.cancel_keyboard(),
        "BROADCAST",
    )


@dp.message(StateFilter(BotState.BROADCAST), F.text)
async def on_broadcast_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text or not _is_admin(message.from_user.id):
        return
    sent = await _notify_subscribers(message.from_user.id, message.text, include_author=True)
    await state.set_state(BotState.MENU)
    logger.info("Рассылка от %s, доставлено %s", message.from_user.id, sent)
    await show_screen(
        message.chat.id,
        message.from_user.id,
        f"Рассылка отправлена: {sent}",
        keyboards.menu_keyboard(True),
        "MENU",
    )


async def _notify_subscribers(author_id: int, text: str, include_author: bool = False) -> int:
    sent = 0
    for user_id, session in all_sessions():
        if not session.get("subscribed"):
            continue
        if user_id == author_id and not include_author:
            continue
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except Exception as error:
            logger.info("Не доставлено %s: %s", user_id, error)
    return sent


async def wave_loop() -> None:
    """Раз в час подписчикам уходит уведомление и рапорт по их башням."""
    while True:
        await asyncio.sleep(WAVE_INTERVAL_SECONDS)
        logger.info("Часовое уведомление о волне")
        for user_id, session in all_sessions():
            if not session.get("subscribed"):
                continue
            report = "Началась новая волна.\n" + simulation.resolve_next_wave(session)
            save_session(user_id, session)
            try:
                await bot.send_message(user_id, report)
            except Exception as error:
                logger.info("Волна не доставлена %s: %s", user_id, error)


@dp.errors()
async def on_error(event: ErrorEvent) -> bool:
    logger.error("Ошибка апдейта: %s", event.exception, exc_info=True)
    return True


async def main() -> None:
    global bot
    if not BOT_TOKEN:
        print("Укажите BOT_TOKEN в файле 02_бот/.env. Пример есть в .env.example.")
        return
    bot = Bot(token=BOT_TOKEN)
    asyncio.create_task(wave_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
