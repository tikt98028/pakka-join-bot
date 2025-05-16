import os
import logging
import asyncio
import aiohttp  # 🆕 для self-ping
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler
)
from dotenv import load_dotenv
from telegram.error import BadRequest

# 🔐 Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"  # 🆕

# 💬
WELCOME_MESSAGE = (
    "🚀 You’ve just unlocked access to Pakka Profit —\n"
    "Where signals = real profits 💸\n\n"
    "🎯 Accuracy up to 98%\n"
    "📈 No experience needed — just copy & earn\n"
    "🎁 Your first signal is 100% FREE\n\n"
    "⏳ Hurry! This free access is available for the next 30 minutes only.\n"
    "After that, signals go private for VIP members.\n\n"
    "👇 Tap now and grab your free signal:\n"
    "➡️ @Pakka_Profit ✅"
)

# 🧠 Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ⚙️ Init FastAPI
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ✅ Handler
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"

    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено запит від {username}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Неможливо схвалити {username}: hide_requester_missing")
        else:
            logging.error(f"❌ Помилка при схваленні {username}: {e}")

    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
        logging.info(f"📬 Повідомлення надіслано {username}")
    except Exception as e:
        logging.warning(f"⚠️ Не вдалося написати {username}: {e}")

# 🔁 Self-ping loop
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(SELF_PING_URL) as resp:
                    logging.info(f"🌐 Self-ping статус: {resp.status}")
            except Exception as e:
                logging.warning(f"🛑 Self-ping помилка: {e}")
            await asyncio.sleep(300)  # кожні 5 хв (300 сек)

# 🚀 Startup
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    logging.info("✅ Webhook встановлено")

    # 🔃 Запуск self-ping
    asyncio.create_task(keep_awake())

# 🧹 Shutdown
@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()

# 📩 Webhook handler
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}
