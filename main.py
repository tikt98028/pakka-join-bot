from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

BOT_TOKEN = "7690353390:AAE4uac_oqNBCjpWJqtapH1tpNqWbU3VjjU"
WELCOME_MESSAGE = "Привіт 👋 Дякую, що приєднався до нашого каналу! Якщо є питання — напиши сюди."

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
    try:
        await context.bot.send_message(chat_id=user.id, text=WELCOME_MESSAGE)
    except:
        print(f"❌ Не вдалося написати @{user.username}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(ChatJoinRequestHandler(approve))
app.run_polling()
