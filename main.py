import os
import logging
import asyncio
import aiohttp
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler,
    CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from telegram.error import BadRequest
from dotenv import load_dotenv

from db import (
    init_db, add_user, get_total_users, get_last_users,
    get_all_user_ids, export_users_to_csv,
    get_users_by_source, get_users_last_24h
)
from sheets import add_user_to_sheet

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
init_db()
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# === KEEP ALIVE ===
async def keep_awake():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(SELF_PING_URL)
                logging.info("🌐 Self-ping успішно")
            except Exception as e:
                logging.warning(f"🛑 Self-ping error: {e}")
            await asyncio.sleep(300)

# === APPROVE ===
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    username = f"@{user.username}" if user.username else f"ID:{user.id}"
    invite = update.chat_join_request.invite_link
    invite_source = invite.name if invite and invite.name else "unknown"
    joined_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Схвалено {username}")
    except BadRequest as e:
        if "hide_requester_missing" in str(e):
            logging.warning(f"⚠️ Неможливо схвалити {username}")
        else:
            logging.error(f"❌ Помилка: {e}")

    add_user(user.id, user.username, user.first_name, invite_source)
    try:
        add_user_to_sheet(user.id, user.username, user.first_name, joined_at, invite_source)
        logging.info(f"📥 Додано до Google Sheets: {user.id} з {invite_source}")
    except Exception as e:
        logging.warning(f"⚠️ Sheets error: {e}")

    # Привітання
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

# === ADMIN PANEL ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔢 Всі користувачі", callback_data="stats")],
        [InlineKeyboardButton("🕓 За добу", callback_data="lastday")],
        [InlineKeyboardButton("📋 Останні", callback_data="logs")],
        [InlineKeyboardButton("📊 Джерела", callback_data="sources")],
        [InlineKeyboardButton("📎 Експорт CSV", callback_data="export")],
        [InlineKeyboardButton("📢 Розсилка", callback_data="broadcast")]
    ])
    await update.message.reply_text("👑 Admin Panel\n\nОберіть дію:", reply_markup=keyboard)

# === CALLBACKS ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        return
    query = update.callback_query
    await query.answer()

    if query.data == "stats":
        count = get_total_users()
        await query.edit_message_text(f"📊 Total approved users: {count}")
    elif query.data == "lastday":
        count = get_users_last_24h()
        await query.edit_message_text(f"🕓 За останні 24 години: {count} користувачів")
    elif query.data == "logs":
        users = get_last_users()
        if not users:
            await query.edit_message_text("⚠️ No users yet.")
            return
        text = "\n".join([
            f"{u[2]} ({u[1] or 'no username'}) — {u[3]}" for u in users
        ])
        await query.edit_message_text(f"📋 Last users:\n{text}")
    elif query.data == "sources":
        sources = get_users_by_source()
        if not sources:
            await query.edit_message_text("⚠️ Даних ще немає.")
            return
        msg = "📊 Джерела приєднань:\n\n"
        for source, count in sources:
            label = source if source else "🔗 Без мітки"
            msg += f"{label}: {count} користувачів\n"
        await query.edit_message_text(msg)
    elif query.data == "export":
        export_users_to_csv()
        try:
            with open("users.csv", "rb") as file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=file,
                    filename="users.csv",
                    caption="📎 Exported user data"
                )
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Export failed: {e}")
    elif query.data == "broadcast":
        await query.edit_message_text("📝 Введи текст розсилки:")
        context.user_data["broadcast_mode"] = True

# === BROADCAST HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
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

# === STARTUP ===
@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(ChatJoinRequestHandler(approve))
    telegram_app.add_handler(CommandHandler("admin", admin_panel))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Бот активний ✅")))
    telegram_app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("🧠 Напиши /admin для керування")))
    telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    asyncio.create_task(keep_awake())
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
