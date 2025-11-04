# src/bot/news.py
from datetime import datetime
from typing import List

import feedparser
import requests

RSS_SOURCES = {
    "general": [
        "https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ],
    "politics": [
        "https://feeds.bbci.co.uk/news/politics/rss.xml",
        "https://lenta.ru/rss/politics",
    ],
    "business": [
        "https://lenta.ru/rss/economics",
        "https://feeds.bbci.co.uk/news/business/rss.xml",
    ],
    "law": [
        "https://lenta.ru/rss/russia",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ],
}


def fetch_rss(url: str) -> List[dict]:
    print(f"[fetch_rss] fetching {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[fetch_rss] ERROR {url}: {e}")
        return []

    feed = feedparser.parse(resp.text)

    items = []
    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        published_raw = getattr(entry, "published", "") or getattr(entry, "updated", "")
        published = published_raw

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
                published = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        if title:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": published,
                }
            )

    print(f"[fetch_rss] got {len(items)} items from {url}")
    return items


def pick_language_variants(items: List[dict], lang: str) -> List[dict]:
    """
    Фильтруем новости по языку пользователя.
    Логика:
    - если lang == "ru": пытаемся взять заголовки с кириллицей
    - иначе: пытаемся взять заголовки без кириллицы (условно "латиница")
    Если после фильтрации пусто — возвращаем исходный список (fallback).
    """

    if not items:
        return items

    def is_cyrillic(text: str) -> bool:
        return any("а" <= ch <= "я" or "А" <= ch <= "Я" for ch in text)

    def is_latin(text: str) -> bool:
        # "латиница" = нет кириллицы вообще
        return not is_cyrillic(text)

    # 1. Выбор целевых новостей по языку
    if lang == "ru":
        preferred = [it for it in items if is_cyrillic(it["title"])]
    else:
        preferred = [it for it in items if is_latin(it["title"])]

    # 2. Если по языку ничего не нашли — fallback: просто отдаём всё
    return preferred or items


def fetch_news(category: str, lang: str) -> str:
    print(f"[fetch_news] category={category} lang={lang}")

    urls = RSS_SOURCES.get(category, RSS_SOURCES["general"])
    print(f"[fetch_news] urls={urls}")

    collected: List[dict] = []
    for url in urls:
        collected.extend(fetch_rss(url))

    # убираем дубли по title
    seen = set()
    unique_items = []
    for it in collected:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique_items.append(it)

    print(f"[fetch_news] total unique before lang filter={len(unique_items)}")

    unique_items = pick_language_variants(unique_items, lang)

    print(f"[fetch_news] after lang filter={len(unique_items)}")

    top_items = unique_items[:5]

    if not top_items:
        print("[fetch_news] RESULT: EMPTY, will return fallback text")
        return "Новостей сейчас нет или источник не отвечает."

    # формируем текст
    lines = ["📰 Сводка свежих новостей:"]
    for i, it in enumerate(top_items, start=1):
        line = f"{i}. {it['title']}"
        if it["published"]:
            line += f" ({it['published']})"
        if it["link"]:
            line += f"\n{it['link']}"
        lines.append(line)
        lines.append("")

    result_text = "\n".join(lines).strip()
    print(f"[fetch_news] RESULT OK, len={len(result_text)} symbols")
    return result_text
