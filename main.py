import os
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler,
    CommandHandler
)
from dotenv import load_dotenv
from telegram.error import BadRequest
from db import init_db, add_user

# === CONFIG ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7926831448
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === INIT ===
init_db()
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# === KEEP AWAKE ===
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(SELF_PING_URL)
                logging.info("🌐 Self-ping успішно")
            except Exception as e:
                logging.warning(f"🛑 Self-ping error: {e}")
            await asyncio.sleep(300)

# === AUTO APPROVE ===
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"
    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено {username}")
    except BadRequest as e:
        logging.warning(f"⚠️ approve error: {e}")
    add_user(user.id, user.username, user.first_name)

    caption = (
        "🚀 You’ve just unlocked access to Pakka Profit —\n"
        "Where signals = real profits 💸\n\n"
        "🎯 Accuracy up to 98%\n"
        "📈 No experience needed — just copy & earn\n"
        "🎁 Your first signal is 100% FREE\n\n"
        "⏳ Hurry! This free access is available for the next 30 minutes only.\n"
        "After that, signals go private for VIP members.\n\n"
        "👇 Tap now and grab your free signal:"
    )
    photo_url = "https://i.postimg.cc/Ssc6hMjG/2025-05-16-13-56-15.jpg"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GET FREE SIGNAL", url="https://t.me/m/nSRnEuc5MjJi")]
    ])
    try:
        await context.bot.send_photo(chat_id=user.id, photo=photo_url, caption=caption, reply_markup=keyboard)
    except Exception as e:
        logging.warning(f"⚠️ send_photo failed: {e}")

# === STARTUP ===
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    telegram_app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Бот активний ✅")))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    asyncio.create_task(keep_awake())
    logging.info("✅ Webhook активовано")

# === SHUTDOWN ===
@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()

# === WEBHOOK ===
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}
