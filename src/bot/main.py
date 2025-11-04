# src/bot/main.py
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from src.bot.config import get_settings
from src.bot.db import DB_PATH, get_user, init_db, upsert_user
from src.bot.logging_setup import setup_logging
from src.bot.news import fetch_news

print(">>> main.py IMPORTED OK")

CATEGORIES = {
    "general": "Общее",
    "politics": "Политика",
    "business": "Экономика",
    "law": "Право",
}

LANGS = {
    "ru": "Русский",
    "en": "English",
    "de": "Deutsch",
    "tr": "Türkçe",
}

FREQUENCIES = {
    "daily_morning": "Каждый день 09:00",
    "daily_evening": "Каждый день 20:00",
    "twice_daily": "2 раза в день (09:00, 20:00)",
}


def kb(chat_id: int) -> InlineKeyboardMarkup:
    u = get_user(chat_id)
    cat = u["category"] if u else "general"
    lang = u["lang"] if u else "ru"
    freq = u["frequency"] if u else "daily_morning"

    cat_row = [
        InlineKeyboardButton(("✅ " if k == cat else "") + v, callback_data=f"set_cat:{k}")
        for k, v in CATEGORIES.items()
    ]
    lang_row = [
        InlineKeyboardButton(("✅ " if k == lang else "") + v, callback_data=f"set_lang:{k}")
        for k, v in LANGS.items()
    ]
    freq_col = [
        [InlineKeyboardButton(("✅ " if k == freq else "") + v, callback_data=f"set_freq:{k}")]
        for k, v in FREQUENCIES.items()
    ]
    now = [InlineKeyboardButton("📰 Прислать сейчас", callback_data="send_now")]

    return InlineKeyboardMarkup([cat_row, lang_row, *freq_col, now])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    upsert_user(chat_id)
    await update.message.reply_text(
        "Привет! Я новостной бот.\n"
        "Открой /settings, чтобы выбрать категорию, язык и частоту.\n"
        "Используй /now чтобы получить свежие новости прямо сейчас."
    )


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "Настройки рассылки:",
        reply_markup=kb(chat_id),
    )


async def now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    u = get_user(chat_id)

    category = u["category"] if u else "general"
    lang = u["lang"] if u else "ru"

    print(f"[now_cmd] chat_id={chat_id} category={category} lang={lang}")

    news_text = fetch_news(category=category, lang=lang)

    print(f"[now_cmd] news_text preview: {news_text[:120]!r}")

    header = (
        "Ваши текущие настройки:\n"
        f"- Категория: {CATEGORIES[category]}\n"
        f"- Язык: {LANGS[lang]}\n\n"
    )

    full_msg = header + news_text

    if update.message:
        await update.message.reply_text(full_msg)
    else:
        await context.bot.send_message(chat_id=chat_id, text=full_msg)


logger = logging.getLogger(__name__)


async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    try:
        await q.answer()
    except BadRequest:
        return

    chat_id = q.message.chat_id
    data = q.data
    print(f"[on_cb] {chat_id=} {data=}")

    if data.startswith("set_cat:"):
        upsert_user(chat_id, category=data.split(":", 1)[1])
    elif data.startswith("set_lang:"):
        upsert_user(chat_id, lang=data.split(":", 1)[1])
    elif data.startswith("set_freq:"):
        upsert_user(chat_id, frequency=data.split(":", 1)[1])
    elif data == "send_now":
        # Жмём кнопку "прислать сейчас"
        await now_cmd(update, context)

    try:
        await q.edit_message_reply_markup(reply_markup=kb(chat_id))
    except BadRequest:
        pass


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning("⚠️ Ошибка Telegram: %s", context.error)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    import sqlite3

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT category, COUNT(*) FROM users GROUP BY category")
        cats = "\n".join([f"{cat}: {count}" for cat, count in c.fetchall()])
        c.execute("SELECT lang, COUNT(*) FROM users GROUP BY lang")
        langs = "\n".join([f"{lang}: {count}" for lang, count in c.fetchall()])
        c.execute("SELECT frequency, COUNT(*) FROM users GROUP BY frequency")
        freqs = "\n".join([f"{freq}: {count}" for freq, count in c.fetchall()])

    text = (
        "📊 *Статистика пользователей:*\n\n"
        f"*Категории:*\n{cats or '—'}\n\n"
        f"*Языки:*\n{langs or '—'}\n\n"
        f"*Частота рассылки:*\n{freqs or '—'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def build_app() -> Application:
    print("[build_app] init...")
    setup_logging()
    cfg = get_settings()
    init_db()

    app = Application.builder().token(cfg.telegram_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("now", now_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_error_handler(on_error)

    print("[build_app] ready")
    return app


def main() -> None:
    print(">>> main() called")
    app = build_app()
    print(">>> build_app() ok, starting polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
