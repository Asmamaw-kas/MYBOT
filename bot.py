import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import asyncio

# ----------------- Logging -----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------- Environment Variables -----------------
TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app.onrender.com/webhook

if not all([TOKEN, PRIVATE_CHANNEL_ID, PUBLIC_CHANNEL, WEBHOOK_URL]):
    missing = [var for var in ["BOT_TOKEN", "PRIVATE_CHANNEL_ID", "PUBLIC_CHANNEL", "WEBHOOK_URL"] if not os.getenv(var)]
    raise ValueError(f"Missing environment variables: {', '.join(missing)}")

bot = Bot(TOKEN)

# ----------------- FastAPI App -----------------
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(req: Request):
    """Receive updates from Telegram webhook"""
    data = await req.json()
    update = Update.de_json(data, bot)
    await app.state.application.update_queue.put(update)
    return {"status": "ok"}

# ----------------- Telegram Bot Handlers -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Get Started", callback_data="get_started")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("Join Channel", url=PUBLIC_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📚 Welcome to Book Bot!\n\nJoin our channel:\n{PUBLIC_CHANNEL}\n\nSend book ID to download\nExample: 123",
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
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text(f"❌ Error. Check ID at {PUBLIC_CHANNEL}")
    else:
        await update.message.reply_text(
            f"📚 Send book ID\nFind IDs at: {PUBLIC_CHANNEL}\nExample: <code>123</code>",
            parse_mode="HTML"
        )

# ----------------- Start Bot -----------------
async def main():
    # Build the bot application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Save application instance to FastAPI app for webhook
    app.state.application = application

    # Set webhook
    await bot.delete_webhook()  # remove any previous webhook
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set to {WEBHOOK_URL}")

    # Run the bot in background (handling updates via webhook)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()  # optional, just for safety
    logger.info("Bot is running...")
    
    # Keep the bot running
    await application.wait_until_stopped()

# ----------------- Run AsyncIO -----------------
if __name__ == "__main__":
    asyncio.run(main())
