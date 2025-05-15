import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

BOT_TOKEN = "7690353390:AAE4uac_oqNBCjpWJqtapH1tpNqWbU3VjjU"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

WELCOME_TEXT = """
👋 *Greetings*, my subscriber *Pakka Profit* 🤝

We are *Attack Team* 🚀  
A group of people who specialize in the *Futures Market* 📈

🧠 Working with our *Signals* and following our *Instructions*,  
💰 You will *always* be in *Profit*.

_Let’s start our cooperation_ 👇  
🔗 Join our channels below:
"""

CHANNEL_LINK = "https://t.me/YOUR_CHANNEL"
SIGNAL_LINK = "https://t.me/c/1544546039/1208"

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.chat_join_request.from_user
        chat_id = update.chat_join_request.chat.id

        # ✅ Автосхвалення
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        logging.info(f"✅ Approved join request from @{user.username or user.id}")

        # 💬 Надсилання привітання
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=WELCOME_TEXT + f"\n\n📲 [SIGNAL]({SIGNAL_LINK})\n📡 [CHANNEL]({CHANNEL_LINK})",
                parse_mode="Markdown"
            )
            logging.info(f"📨 Sent welcome message to @{user.username or user.id}")
        except Exception as dm_error:
            logging.warning(f"⚠️ Could not DM user: {dm_error}")

    except Exception as e:
        logging.error(f"❌ Error approving join request: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.run_polling()
