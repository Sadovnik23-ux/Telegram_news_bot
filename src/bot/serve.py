# src/bot/serve.py
import asyncio
import os

from fastapi import FastAPI

from .main import build_app

app = FastAPI()


@app.get("/")
@app.get("/health")
def health():
    return {"ok": True}


async def run_bot():
    application = build_app()
    await application.run_polling()


if __name__ == "__main__":
    import uvicorn

    asyncio.get_event_loop().create_task(run_bot())

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
