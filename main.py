import os
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler
)
from dotenv import load_dotenv
from telegram.error import BadRequest

# 🔐 Завантажуємо токен
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"  # 👈 Для анти-сну

# 🧠 Налаштування логів
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Ініціалізація FastAPI і Telegram bot
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# 🔁 Пінг бота щоб не засинав
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(SELF_PING_URL) as resp:
                    logging.info(f"🌐 Self-ping: {resp.status}")
            except Exception as e:
                logging.warning(f"🛑 Self-ping error: {e}")
            await asyncio.sleep(300)  # кожні 5 хв

# ✅ Обробка нових учасників
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"

    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено запит від {username}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Telegram не дозволяє схвалити {username}")
        else:
            logging.error(f"❌ Помилка при схваленні {username}: {e}")

    # ✉️ Повідомлення + кнопка
    text = (
        "🚀 You’ve just unlocked access to Pakka Profit —\n"
        "Where signals = real profits 💸\n\n"
        "🎯 Accuracy up to 98%\n"
        "📈 No experience needed — just copy & earn\n"
        "🎁 Your first signal is 100% FREE\n\n"
        "⏳ Hurry! This free access is available for the next 30 minutes only.\n"
        "After that, signals go private for VIP members.\n\n"
        "👇 Tap now and grab your free signal:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GET FREE SIGNAL", url="https://t.me/m/nSRnEuc5MjJi")]
    ])

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=keyboard
        )
        logging.info(f"📬 Повідомлення надіслано {username}")
    except Exception as e:
        logging.warning(f"⚠️ Не вдалося написати {username}: {e}")

# 🚀 Запуск
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    logging.info("✅ Webhook встановлено")
    asyncio.create_task(keep_awake())  # Запуск self-ping

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
