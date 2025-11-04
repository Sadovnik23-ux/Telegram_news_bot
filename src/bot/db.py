# src/bot/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("newsbot.sqlite3")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            category TEXT DEFAULT 'general',
            lang TEXT DEFAULT 'ru',
            frequency TEXT DEFAULT 'daily_morning',
            enabled INTEGER DEFAULT 1
        );
        """
        )
        conn.commit()


def get_user(chat_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
        return c.fetchone()


def upsert_user(chat_id: int, **fields):
    if not fields:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users(chat_id) VALUES(?)", (chat_id,))
            conn.commit()
        return
    sets = ", ".join([f"{k}=?" for k in fields])
    vals = list(fields.values()) + [chat_id]
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users(chat_id) VALUES(?)", (chat_id,))
        c.execute(f"UPDATE users SET {sets} WHERE chat_id=?", vals)
        conn.commit()
