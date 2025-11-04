# src/bot/serve.py
import asyncio
from contextlib import suppress

from fastapi import FastAPI

from .main import build_app  # берём сборку ptb-приложения

app = FastAPI()


@app.get("/")
@app.get("/health")
def health():
    return {"ok": True}


async def run_bot():
    application = build_app()
    # v21 — run_polling() асинхронный
    await application.run_polling()


@app.on_event("startup")
async def _startup():
    # запускаем телеграм-бота фоном и сохраняем таск
    app.state.bot_task = asyncio.create_task(run_bot())


@app.on_event("shutdown")
async def _shutdown():
    # корректно останавливаем бота при выключении сервиса
    task = getattr(app.state, "bot_task", None)
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
