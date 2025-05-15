from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram import Update
from flask import Flask
import asyncio
import os

BOT_TOKEN = "7690353390:AAE4uac_oqNBCjpWJqtapH1tpNqWbU3VjjU"  # ← Замінити на свій реальний токен
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання – напиши сюди."

app = Flask(__name__)

@app.route("/")
def home():
    return "I am alive!"

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.chat_join_request.from_user
        chat_id = update.chat_join_request.chat.id
        await context.bot.approve_chat_join_request(chat_id, user.id)
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
    except Exception as e:
        print(f"❌ Не вдалось написати @{user.username}, помилка: {e}")

async def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(ChatJoinRequestHandler(approve))
    await application.run_polling()

def run():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    run()
