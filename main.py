import os
import asyncio
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Logger Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("TelegramBot")

# --- Environment Configuration ---
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') # TEMPORARILY COMMENT OUT
WEBHOOK_SECRET_TOKEN = os.environ.get('WEBHOOK_SECRET_TOKEN')

# Removed the check for GOOGLE_API_KEY as it's commented out for now
if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL or not WEBHOOK_SECRET_TOKEN:
    raise ValueError("Missing required environment variables (TELEGRAM_BOT_TOKEN, WEBHOOK_URL, WEBHOOK_SECRET_TOKEN)")

PORT = int(os.environ.get('PORT', 8443)) # Render sets PORT=10000, so this should pick it up correctly

# --- Gemini Model Setup (TEMPORARILY COMMENT OUT THESE LINES) ---
# import google.generativeai as genai
# genai.configure(api_key=GOOGLE_API_KEY)
# model = genai.GenerativeModel('gemini-pro')
# conversations = {}

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_id = update.effective_chat.id # Get chat_id here
    logger.info(f"Received /start command from {user.id} (chat_id={chat_id})") # Added log for chat_id
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I received your /start message. This is a basic test reply.",
        # reply_markup=ForceReply(selective=True), # Can remove for simplicity
    )
    logger.info(f"Sent /start reply to {user.id}")

# Simplified generate_response for testing message receipt
async def generate_response(update: Update, context):
    chat_id = update.effective_chat.id
    user_message = update.message.text if update.message else None

    if not user_message:
        logger.info(f"Non-text or empty message from chat_id={chat_id}")
        return

    logger.info(f"Received ANY message from chat_id={chat_id}: '{user_message}' - This is a simple test!")

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Hello! I received your message: '{user_message}'. This is a basic test reply.",
    )
    logger.info(f"Sent basic test reply to chat_id={chat_id}")


async def set_webhook():
    """Set webhook for production environment."""
    if WEBHOOK_URL:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            secret_token=WEBHOOK_SECRET_TOKEN
        )
        logger.info("Webhook set successfully")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_response))

    # Start the Bot
    if WEBHOOK_URL:
        logger.info("Starting in production mode with webhook")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            secret_token=WEBHOOK_SECRET_TOKEN,
            cert='cert.pem' if os.path.exists('cert.pem') else None
        )
    else:
        logger.info("Starting in development mode with polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() # Call main() directly
