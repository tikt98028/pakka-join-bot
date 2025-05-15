from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from flask import Flask
from threading import Thread
import asyncio

BOT_TOKEN = "7690355390:AAE4uas_oqNBCjpwJdtapH1tqNqWbU3VjjU"
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання — напиши сюди."

app = Flask(__name__)

@app.route("/")
def home():
    return "I am alive!"

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
    except:
        print(f"❌ Не вдалося написати @{user.username}")

def run_flask():
    app.run(host="0.0.0.0", port=10000)

def run_telegram_bot():
    asyncio.run(start_bot())

async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(approve))
    await app.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_telegram_bot()
