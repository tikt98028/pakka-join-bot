import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from dotenv import load_dotenv

# Завантажуємо токен з .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання — напиши сюди."

# Увімкнення логів
logging.basicConfig(level=logging.INFO)

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id

    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
    
    username = f"@{user.username}" if user.username else f"ID:{user.id}"
    logging.info(f"✅ Схвалено запит від {username}")

    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
    except:
        logging.warning(f"❌ Не вдалося написати {username}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(ChatJoinRequestHandler(approve))
app.run_polling()
