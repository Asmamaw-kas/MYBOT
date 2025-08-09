import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from fastapi import FastAPI
import threading
import uvicorn

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FastAPI health check
app = FastAPI()
@app.get("/")
def health_check():
    return {"status": "ok"}

# Load environment variables
TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL")

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
        "Send book ID to download\nExample: 123",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_started":
        await query.edit_message_text(
            text=f"📖 How to download:\n\n1. Find IDs in:\n{PUBLIC_CHANNEL}\n\n2. Send book ID\nExample: <code>123</code>",
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
            logger.error(f"Error: {e}")
            await update.message.reply_text(f"❌ Error. Check ID at {PUBLIC_CHANNEL}")
    else:
        await update.message.reply_text(
            f"📚 Send book ID\nFind IDs at: {PUBLIC_CHANNEL}\nExample: <code>123</code>",
            parse_mode="HTML"
        )

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def main():
    try:
        # Verify environment variables
        if not all([TOKEN, PRIVATE_CHANNEL_ID, PUBLIC_CHANNEL]):
            missing = []
            if not TOKEN: missing.append("BOT_TOKEN")
            if not PRIVATE_CHANNEL_ID: missing.append("PRIVATE_CHANNEL_ID")
            if not PUBLIC_CHANNEL: missing.append("PUBLIC_CHANNEL")
            logger.error(f"Missing: {', '.join(missing)}")
            raise ValueError(f"Missing: {', '.join(missing)}")

        # Start health check server
        threading.Thread(target=run_fastapi, daemon=True).start()

        # Start bot
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("Starting bot...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()
