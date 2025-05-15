import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# 🔐 ВСТАВ СЮДИ СВІЙ ТОКЕН
BOT_TOKEN = "7690353390:AAE4uac_oqNBCjpWJqtapH1tpNqWbU3VjjU"

# 🔍 Логування для відладки (опціонально)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 📥 Обробник join-запитів
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=update.chat_join_request.from_user.id,
        )
        logging.info(
            f"✅ Запит від @{update.chat_join_request.from_user.username or update.chat_join_request.from_user.id} підтверджено."
        )
    except Exception as e:
        logging.error(f"❌ Помилка при підтвердженні запиту: {e}")

# 🚀 Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.run_polling()
