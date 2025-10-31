import logging
import os
import threading
import time
import requests
import uvicorn
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ─────────────────────────────
#  LOGGING
# ─────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────
#  FASTAPI APP
# ─────────────────────────────
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Bot is running!"}

# ─────────────────────────────
#  ENVIRONMENT VARIABLES
# ─────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL")

# ─────────────────────────────
#  TELEGRAM COMMAND HANDLERS
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Get Started", callback_data="get_started")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("Join Channel", url=PUBLIC_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 Welcome to Book Bot!\n\n"
        f"Join our channel:\n{PUBLIC_CHANNEL}\n\n"
        "Send a book ID to download.\nExample: 123",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_started":
        await query.edit_message_text(
            text=f"📖 How to download:\n\n1. Find book IDs in:\n{PUBLIC_CHANNEL}\n\n2. Send the ID like: <code>123</code>",
            parse_mode="HTML"
        )
    elif query.data == "help":
        await query.edit_message_text(
            text=f"ℹ️ Help:\n• Send book ID to download\n• Find IDs in: {PUBLIC_CHANNEL}",
            parse_mode="HTML"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        try:
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=int(PRIVATE_CHANNEL_ID),
                message_id=int(text)
            )
            await update.message.reply_text("✅ Book sent!")
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text(f"❌ Error. Check ID at {PUBLIC_CHANNEL}")
    else:
        await update.message.reply_text(
            f"📚 Send a valid book ID\nFind IDs at: {PUBLIC_CHANNEL}\nExample: <code>123</code>",
            parse_mode="HTML"
        )

# ─────────────────────────────
#  KEEP ALIVE SYSTEM
# ─────────────────────────────
def keep_alive():
    """Ping the Render web service every 5 minutes to prevent sleeping."""
    url = "https://your-app-name.onrender.com"  # 🔁 Replace with your Render URL
    while True:
        try:
            requests.get(url)
            logger.info("Pinged Render to keep alive.")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        time.sleep(300)  # every 5 minutes

# ─────────────────────────────
#  RUN FASTAPI
# ─────────────────────────────
def run_fastapi():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# ─────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────
def main():
    if not all([TOKEN, PRIVATE_CHANNEL_ID, PUBLIC_CHANNEL]):
        missing = []
        if not TOKEN: missing.append("BOT_TOKEN")
        if not PRIVATE_CHANNEL_ID: missing.append("PRIVATE_CHANNEL_ID")
        if not PUBLIC_CHANNEL: missing.append("PUBLIC_CHANNEL")
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        raise ValueError(f"Missing: {', '.join(missing)}")

    # Start FastAPI in background
    threading.Thread(target=run_fastapi, daemon=True).start()

    # Start keep-alive ping thread
    threading.Thread(target=keep_alive, daemon=True).start()

    # Start Telegram bot
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()
