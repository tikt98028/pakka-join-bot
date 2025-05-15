import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, ChatJoinRequestHandler
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання — напиши сюди."

logging.basicConfig(level=logging.INFO)

app = FastAPI()

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

@app.on_event("startup")
async def on_startup():
    await telegram_app.bot.set_webhook(url=f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}")
    logging.info("✅ Webhook встановлено")
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    await telegram_app.initialize()
    await telegram_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"
    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
    logging.info(f"✅ Схвалено запит від {username}")
    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
    except:
        logging.warning(f"❌ Не вдалося написати {username}")
