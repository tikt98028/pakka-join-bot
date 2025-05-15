from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from flask import Flask
from threading import Thread
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання — напиши сюди."

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
    except:
        print(f"❌ Не вдалося написати @{user.username}")

def run_telegram_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(approve))
    app.run_async()

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return 'I am alive!'

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

Thread(target=run_telegram_bot).start()
Thread(target=run_flask).start()
