import os
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler,
    CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from telegram.error import BadRequest
from dotenv import load_dotenv
from datetime import datetime

from db import (
    init_db, add_user, get_total_users, get_last_users,
    get_all_user_ids, export_users_to_csv
)
from sheets import add_user_to_sheet

# === CONFIG ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7926831448  # заміни на свій
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

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
    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено {user.username or user.id}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Неможливо схвалити {user.username or user.id}")
        else:
            logging.error(f"❌ Помилка: {e}")
    add_user(user.id, user.username, user.first_name)

    # Додаємо дату
    joined_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    try:
        add_user_to_sheet(user.id, user.username, user.first_name, joined_at)
        logging.info("📥 Додано до Google Sheets")
    except Exception as e:
        logging.warning(f"⚠️ Sheets error: {e}")

    # Привітання
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GET FREE SIGNAL", url="https://t.me/m/nSRnEuc5MjJi")]
    ])
    try:
        await context.bot.send_photo(
            chat_id=user.id,
            photo="https://i.postimg.cc/Ssc6hMjG/2025-05-16-13-56-15.jpg",
            caption="🚀 Welcome to Pakka Profit 💸\n⏳ Free for 30 min only!",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.warning(f"⚠️ send_photo failed: {e}")

# === ADMIN ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔢 Статистика", callback_data="stats")],
        [InlineKeyboardButton("📋 Останні", callback_data="logs")],
        [InlineKeyboardButton("📢 Розсилка", callback_data="broadcast")],
        [InlineKeyboardButton("📎 CSV", callback_data="export")]
    ])
    await update.message.reply_text("👑 Admin Panel:", reply_markup=keyboard)

# === CALLBACK ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    query = update.callback_query
    await query.answer()
    if query.data == "stats":
        count = get_total_users()
        await query.edit_message_text(f"📊 Users: {count}")
    elif query.data == "logs":
        users = get_last_users()
        text = "\n".join([f"{u[2]} (@{u[1]}) — {u[3]}" for u in users])
        await query.edit_message_text(f"📋 Users:\n{text}")
    elif query.data == "broadcast":
        context.user_data["broadcast_mode"] = True
        await query.edit_message_text("📝 Введи текст:")
    elif query.data == "export":
        export_users_to_csv()
        with open("users.csv", "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename="users.csv"
            )

# === BROADCAST ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.user_data.get("broadcast_mode"):
        text = "🗣 " + update.message.text
        success, fail = 0, 0
        for uid in get_all_user_ids():
            try:
                await context.bot.send_message(chat_id=uid, text=text)
                success += 1
            except:
                fail += 1
        await update.message.reply_text(f"📤 Sent: {success}, Failed: {fail}")
        context.user_data["broadcast_mode"] = False

# === STARTUP / SHUTDOWN ===
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    telegram_app.add_handler(CommandHandler("admin", admin_panel))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Бот активний ✅")))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(keep_awake())

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
