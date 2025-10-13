import os
import logging
import asyncio
import aiohttp
from datetime import datetime
from pytz import timezone
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler,
    CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from telegram.error import BadRequest
from dotenv import load_dotenv

from sheets import (
    add_user_to_sheet, get_total_users,
    get_last_users, get_users_today,
    get_users_by_source, get_all_user_ids,
    count_by_source, get_users_today_by_source
)
from facebook import send_facebook_event  # <-- Додано імпорт

# === CONFIG ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7926831448))
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === INIT ===
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# === KEEP ALIVE ===
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(SELF_PING_URL)
                logging.info("\U0001F310 Self-ping успішно")
            except Exception as e:
                logging.warning(f"\U0001F6D1 Self-ping error: {e}")
            await asyncio.sleep(300)

# === DAILY REPORT ===
async def send_daily_report(bot):
    await asyncio.sleep(30)
    while True:
        try:
            stats = get_users_today_by_source()
            if not stats:
                text = "📅 Звіт за день:\n\n❌ Немає нових користувачів."
            else:
                text = "📅 Звіт за сьогодні (за Києвом):\n\n"
                for source, count in stats:
                    label = source if source else "unknown"
                    text += f"🔗 {label} — {count}\n"
            await bot.send_message(chat_id=ADMIN_ID, text=text)
        except Exception as e:
            logging.warning(f"❌ Daily report error: {e}")
        await asyncio.sleep(86400)

# === APPROVE JOIN REQUEST ===
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"
    invite = update.chat_join_request.invite_link
    invite_source = invite.name if invite and invite.name else "unknown"

    # Київський час
    kyiv_time = datetime.now(timezone("Europe/Kyiv"))
    joined_at = kyiv_time.strftime('%Y-%m-%d %H:%M:%S')

    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено {username}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Неможливо схвалити {username}")
        else:
            logging.error(f"❌ Помилка: {e}")

    try:
        add_user_to_sheet(user.id, user.username, user.first_name, joined_at, invite_source)
        logging.info(f"📅 Додано до Google Sheets: {user.id} з {invite_source}")

        # === Facebook Conversion API ===
        event_id = context.user_data.get("event_id")
        send_facebook_event(
            event_id=event_id,
            user_data={
                "email": None,
                "phone": None,
                "first_name": user.first_name,
                "last_name": None
            }
        )

    except Exception as e:
        logging.warning(f"⚠️ Sheets/Facebook error: {e}")

    photo_url = "https://i.postimg.cc/Ssc6hMjG/2025-05-16-13-56-15.jpg"
    caption = (
        "🚀 You’ve just unlocked access to Pakka Profit —\n"
        "Where signals = real profits 💸\n\n"
        "🌟 Accuracy up to 98%\n"
        "📈 No experience needed — just copy & earn\n\n"
        "🏱 Your first signal is 100% FREE\n\n"
        "⏳ Hurry! This free access is available for the next 30 minutes only.\n"
        "After that, signals go private for VIP members.\n\n"
        "🔻 Tap now and grab your free signal:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GET FREE SIGNAL", url="https://t.me/m/bBXst0VWZjAy")]
    ])
    try:
        await context.bot.send_photo(
            chat_id=user.id,
            photo=photo_url,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.warning(f"⚠️ send_photo failed: {e}")

# === START HANDLER ===
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        context.user_data['event_id'] = context.args[0]
    await update.message.reply_text("Бот активний ✅")

# === ІНШІ ХЕНДЛЕРИ (без змін) ===

# ... (залиш решту без змін)

@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    telegram_app.add_handler(CommandHandler("admin", admin_panel))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(CommandHandler("start", start_handler))  # оновлено
    telegram_app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("🧠 Напиши /admin для керування")))
    telegram_app.add_handler(CommandHandler("stats", stats_handler))
    telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)

    asyncio.create_task(keep_awake())
    asyncio.create_task(send_daily_report(telegram_app.bot))

    logging.info("✅ Webhook активовано")

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}
