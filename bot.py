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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables (set in Railway)
TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID"))
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("📚 Get Started", callback_data="get_started")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("Join Channel", url=PUBLIC_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📚 Welcome to Book Bot!\n\n"
        f"Join our channel for all available books:\n{PUBLIC_CHANNEL}\n\n"
        "To get a book, just send me the book ID\n"
        "Example: 123",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    if query.data == "get_started":
        await query.edit_message_text(
            text="📖 How to download books:\n\n"
                 f"1. Find book IDs in our channel:\n{PUBLIC_CHANNEL}\n\n"
                 "2. Just send me the book ID number\n\n"
                 "Example: <code>123</code>",
            parse_mode="HTML"
        )
    elif query.data == "help":
        await query.edit_message_text(
            text="ℹ️ Help Information\n\n"
                 "• Just send the book ID to download\n"
                 "• Book IDs are shown in our channel posts\n"
                 f"• Channel: {PUBLIC_CHANNEL}\n"
                 "• Contact admin for support",
            parse_mode="HTML"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user sends a book ID"""
    text = update.message.text.strip()

    if text.isdigit():
        try:
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=PRIVATE_CHANNEL_ID,
                message_id=int(text)
            )
            await update.message.reply_text("✅ Book sent successfully!")
        except Exception as e:
            logger.error(f"Error forwarding book: {e}")
            await update.message.reply_text(
                "❌ Book not found. Please check the ID and try again.\n"
                f"Find correct IDs in our channel: {PUBLIC_CHANNEL}"
            )
    else:
        await update.message.reply_text(
            "📚 Send me a book ID to get the book\n\n"
            f"Find book IDs in our channel: {PUBLIC_CHANNEL}\n\n"
            "Example: <code>123</code>",
            parse_mode="HTML"
        )

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
