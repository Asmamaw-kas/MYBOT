import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import uvicorn

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
    """Health check endpoint to keep Render alive"""
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(req: Request):
    """Receive Telegram updates via webhook"""
    data = await req.json()
    update = Update.de_json(data, bot)
    await app.state.application.update_queue.put(update)
    return {"status": "ok"}

# ----------------- Telegram Handlers -----------------
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
async def start_bot():
    """Initialize bot, set webhook, and keep running"""
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Save app instance to FastAPI for webhook usage
    app.state.application = application

    # Set Telegram webhook
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set to {WEBHOOK_URL}")

    # Initialize and start the application
    await application.initialize()
    await application.start()
    logger.info("Bot is running via webhook...")

    # Keep bot alive forever
    await asyncio.Event().wait()  # Infinite wait to prevent stopping

# ----------------- Run FastAPI + Bot -----------------
async def main():
    # Start bot in background
    asyncio.create_task(start_bot())

    # Start FastAPI server on Render's assigned port
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting FastAPI on port {port}")
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
