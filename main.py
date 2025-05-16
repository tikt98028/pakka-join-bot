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
from db import init_db, add_user, get_total_users, get_last_users, get_all_user_ids

# ===🔐 Config ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7926831448
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"

# ===🧠 Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ===🧠 Init ===
init_db()
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ===💤 Keep alive ===
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(SELF_PING_URL) as resp:
                    logging.info(f"🌐 Self-ping: {resp.status}")
            except Exception as e:
                logging.warning(f"🛑 Self-ping error: {e}")
            await asyncio.sleep(300)

# ===🤖 Approve new user ===
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"

    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено {username}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Неможливо схвалити {username}")
        else:
            logging.error(f"❌ Інша помилка: {e}")

    # 💾 Додаємо в БД
    add_user(user.id, user.username, user.first_name)

    # ✉️ Надсилання фото + кнопка
    photo_url = "https://i.postimg.cc/Ssc6hMjG/2025-05-16-13-56-15.jpg"
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
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GET FREE SIGNAL", url="https://t.me/m/nSRnEuc5MjJi")]
    ])
    try:
        await context.bot.send_photo(
            chat_id=user.id,
            photo=photo_url,
            caption=caption,
            reply_markup=keyboard
        )
        logging.info(f"📬 Повідомлення надіслано {username}")
    except Exception as e:
        logging.warning(f"⚠️ Не вдалося надіслати {username}: {e}")

# ===🛡️ Admin check ===
def is_admin(user_id):
    return user_id == ADMIN_ID

# ===📊 /status ===
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    count = get_total_users()
    await update.message.reply_text(f"📊 Total approved users: {count}")

# ===📋 /log ===
async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    rows = get_last_users()
    if not rows:
        await update.message.reply_text("⚠️ No users yet.")
        return
    msg = "\n".join(
        [f"{r[2]} ({r[1] or 'no username'}) — {r[3]}" for r in rows]
    )
    await update.message.reply_text(f"📋 Last users:\n{msg}")

# ===📢 /broadcast [msg] ===
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("❗ Usage: /broadcast your message")
        return
    text = "🗣 " + " ".join(context.args)
    ids = get_all_user_ids()
    success, fail = 0, 0
    for uid in ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
        except:
            fail += 1
    await update.message.reply_text(f"📤 Done: {success} ✅ | Failed: {fail} ❌")

# ===ℹ️ /help ===
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(
        "👑 Admin Commands:\n"
        "/status — users count\n"
        "/log — last 5 users\n"
        "/broadcast [msg] — mass send\n"
        "/help — this list"
    )

# ===🚀 Startup ===
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    telegram_app.add_handler(CommandHandler("status", status))
    telegram_app.add_handler(CommandHandler("log", log))
    telegram_app.add_handler(CommandHandler("broadcast", broadcast))
    telegram_app.add_handler(CommandHandler("help", help_cmd))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    asyncio.create_task(keep_awake())
    logging.info("✅ Webhook активовано")

# ===🧹 Shutdown ===
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
