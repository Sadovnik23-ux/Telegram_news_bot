import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    default_tz: str
    newsapi_key: str | None


def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Put it into .env")
    return Settings(
        telegram_token=token,
        default_tz=os.getenv("DEFAULT_TZ", "UTC").strip(),
        newsapi_key=os.getenv("NEWSAPI_KEY", "").strip() or None,
    )
