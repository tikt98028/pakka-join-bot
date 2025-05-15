import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler
)
from dotenv import load_dotenv
from telegram.error import BadRequest

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання — напиши сюди."

# 🔇 Логування тільки INFO та вище
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# 👥 Головна функція обробки запитів
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"

    # ✅ Спроба схвалити юзера
    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено запит від {username}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Telegram не дозволяє схвалити {username}: hide_requester_missing")
        else:
            logging.error(f"❌ Помилка при схваленні {username}: {e}")

    # ✅ Спроба надіслати привітання
    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
        logging.info(f"📬 Повідомлення надіслано {username}")
    except Exception as e:
        logging.warning(f"⚠️ Не вдалося написати {username}: {e}")

# 🚀 Webhook setup
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    logging.info("✅ Webhook встановлено")

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
