import os
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler,
    CommandHandler, CallbackQueryHandler
)
from dotenv import load_dotenv
from telegram.error import BadRequest
from db import init_db, add_user, get_total_users, get_last_users, get_all_user_ids

# === Config ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7926831448
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://pakka-join-bot.onrender.com{WEBHOOK_PATH}"
SELF_PING_URL = "https://pakka-join-bot.onrender.com"

# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === Init ===
init_db()
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Self-ping ===
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(SELF_PING_URL)
                logging.info("🌐 Self-ping успішно")
            except Exception as e:
                logging.warning(f"🛑 Self-ping error: {e}")
            await asyncio.sleep(300)

# === Approve new users ===
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
            logging.error(f"❌ Помилка: {e}")
    add_user(user.id, user.username, user.first_name)

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
    except Exception as e:
        logging.warning(f"⚠️ send_photo failed: {e}")

# === Admin Panel (/admin) ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔢 Статистика", callback_data="stats")],
        [InlineKeyboardButton("📋 Останні користувачі", callback_data="logs")],
        [InlineKeyboardButton("📢 Розсилка", callback_data="broadcast")]
    ])
    await update.message.reply_text("👑 Admin Panel\n\nОберіть дію:", reply_markup=keyboard)

# === Обробка кнопок ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    query = update.callback_query
    await query.answer()
    if query.data == "stats":
        count = get_total_users()
        await query.edit_message_text(f"📊 Total approved users: {count}")
    elif query.data == "logs":
        users = get_last_users()
        if not users:
            await query.edit_message_text("⚠️ No users yet.")
            return
        text = "\n".join([
            f"{u[2]} ({u[1] or 'no username'}) — {u[3]}" for u in users
        ])
        await query.edit_message_text(f"📋 Last users:\n{text}")
    elif query.data == "broadcast":
        await query.edit_message_text("📝 Введи текст розсилки:")
        context.user_data["broadcast_mode"] = True

# === Обробка повідомлень для розсилки ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.user_data.get("broadcast_mode"):
        text = "🗣 " + update.message.text
        ids = get_all_user_ids()
        sent, fail = 0, 0
        for uid in ids:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
                sent += 1
            except:
                fail += 1
        await update.message.reply_text(f"📤 Done: {sent} sent, {fail} failed")
        context.user_data["broadcast_mode"] = False

# === Startup ===
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    telegram_app.add_handler(CommandHandler("admin", admin_panel))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Бот активний ✅")))
    telegram_app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("🧠 Напиши /admin для керування")))
    telegram_app.add_handler(MessageHandler(None, handle_message))  # для розсилки
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    asyncio.create_task(keep_awake())
    logging.info("✅ Webhook активовано")

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
