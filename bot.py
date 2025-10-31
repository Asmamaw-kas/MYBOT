# main.py
import os
import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- ENV ----------
TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app.onrender.com/webhook

if not all([TOKEN, PRIVATE_CHANNEL_ID, PUBLIC_CHANNEL, WEBHOOK_URL]):
    missing = [k for k,v in {
        "BOT_TOKEN": TOKEN,
        "PRIVATE_CHANNEL_ID": PRIVATE_CHANNEL_ID,
        "PUBLIC_CHANNEL": PUBLIC_CHANNEL,
        "WEBHOOK_URL": WEBHOOK_URL
    }.items() if not v]
    raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

bot = Bot(TOKEN)
app = FastAPI()

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📚 Get Started", callback_data="get_started")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("Join Channel", url=PUBLIC_CHANNEL)],
    ]
    await update.message.reply_text(
        f"📚 Welcome!\nJoin: {PUBLIC_CHANNEL}\nSend book ID (e.g. 123)",
        reply_markup=InlineKeyboardMarkup(kb),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_started":
        await query.edit_message_text(
            f"📖 Send book ID (from {PUBLIC_CHANNEL}). Example: <code>123</code>",
            parse_mode="HTML",
        )
    else:
        await query.edit_message_text("ℹ️ Help: send book ID.", parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if text.isdigit():
        try:
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=int(PRIVATE_CHANNEL_ID),
                message_id=int(text),
            )
            await update.message.reply_text("✅ Book sent!")
        except Exception as e:
            logger.exception("Forward failed")
            await update.message.reply_text(f"❌ Error. Check ID at {PUBLIC_CHANNEL}")
    else:
        await update.message.reply_text(
            f"📚 Send a numeric book ID. Find IDs at {PUBLIC_CHANNEL}",
            parse_mode="HTML",
        )

# ---------- Webhook endpoint ----------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram will POST updates here (HTTPS required)."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    update = Update.de_json(payload, bot)
    # application is stored in app.state (set on startup)
    application = getattr(app.state, "telegram_app", None)
    if not application:
        # If bot isn't ready, return 503 so Telegram retries
        raise HTTPException(status_code=503, detail="Bot not ready")
    # Put the update into the bot's update queue for processing
    await application.update_queue.put(update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}

# ---------- Start and shutdown lifecycle ----------
@app.on_event("startup")
async def on_startup():
    logger.info("FastAPI startup: initializing Telegram application")
    application = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Store application on fastapi app so webhook route can access it
    app.state.telegram_app = application

    # set webhook (replace existing)
    await bot.delete_webhook(drop_pending_updates=True)
    ok = await bot.set_webhook(WEBHOOK_URL)
    if not ok:
        logger.warning("set_webhook returned False")
    else:
        logger.info(f"Webhook set to {WEBHOOK_URL}")

    # initialize and start the application (run handlers in background)
    await application.initialize()
    await application.start()
    logger.info("Telegram application started (webhook mode)")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutdown: stopping Telegram application and deleting webhook")
    application = getattr(app.state, "telegram_app", None)
    if application:
        await application.stop()
        await application.shutdown()
    try:
        await bot.delete_webhook(drop_pending_updates=False)
    except Exception:
        logger.exception("Failed to delete webhook during shutdown")

# ---------- Run Uvicorn (entrypoint) ----------
def run():
    port = int(os.environ.get("PORT", 8000))
    # uvicorn.run is blocking and will bind the port Render expects
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    run()
