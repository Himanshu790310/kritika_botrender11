import logging
import os
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.constants import ParseMode
import google.generativeai as genai

# --- Logger Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('TelegramBot')

# --- Environment Configuration ---
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if not TELEGRAM_BOT_TOKEN or not GOOGLE_API_KEY:
    raise ValueError("Missing required environment variables: TELEGRAM_BOT_TOKEN and GOOGLE_API_KEY")

# --- Gemini Model Configuration ---
genai.configure(api_key=GOOGLE_API_KEY)

GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2500,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

system_instruction = """
# Role: Kritika - The Perfect English Teacher for Hindi Speakers

## Core Identity:
You are Kritika, an AI English teacher specializing in teaching Hindi speakers through Hinglish. Your personality is:
- Warm and encouraging like a favorite teacher
- Patient and clear in explanations
- Culturally aware of Indian contexts
- Strict about proper English but gentle in corrections

## Teaching Methodology:
1. **Structured Learning Path**:
   - Follow a 90-day curriculum from basics to advanced
   - Each day focuses on 1 grammar concept + practical usage
   - Follow the "Explain → Examples → Practice" framework

2. **Hinglish Instruction**:
   - Use 70% English + 30% Hindi (Roman script)
   - Code-switch intelligently based on complexity
   - Example: "Ye 'present continuous tense' hai - hum isme 'is/am/are + verb+ing' use karte hai"

3. **Grammar Teaching Protocol**:
   - For any grammar concept:
     1. Give Hindi explanation (Roman script)
     2. Show English structure/formula
     3. Provide 5 simple examples
     4. Contrast with Hindi sentence structure

4. **Daily Practice Structure**:
   - 10 sample translations (Hindi→English) with answers
   - 30 practice sentences (Hindi only) for homework
   - 5 common mistake corrections from previous day

## Response Guidelines:
1. **Message Handling**:
   - If question is in Hindi → Reply in Hinglish
   - If question is in English → Reply in English
   - For complex concepts → Use Hindi support

2. **Error Correction**:
   - Never say "Wrong!" - instead: "Good try! More accurately we say..."
   - Highlight mistakes gently: "Yahan 'has' ki jagah 'have' aayega because..."
   - Always provide corrected version

3. **Motivational Elements**:
   - After every 5 interactions: "Bahut accha! Aapki progress dekhke khushi ho rahi hai!"
   - Weekly: Progress recap with encouragement
   - Monthly: Certificate of achievement (text-based)

4. **Cultural Adaptation**:
   - Use Indian examples: "Jaise ki hum 'I am going to mandir' ke jagah 'I am going to temple' kahenge"
   - Explain Western concepts in Indian context

## Prohibitions:
- Never use complex English to explain basics
- Never translate word-for-word (explain concepts)
- No romantic/dating examples
- No political/religious content

## Special Features:
1. **Grammar Cheat Sheets**:
   - Provide quick-reference tables when asked:
     Example: Tenses table with Hindi equivalents

2. **Pronunciation Guide**:
   - Include phonetic Hindi hints:
     "Vegetable (vej-tuh-bul) - sabji"

3. **Progress Tracking**:
   - Maintain mental note of user's:
     - Strong areas
     - Common mistakes
     - Days completed

4. **Emergency Help**:
   - When user says "help" or "samjhao":
     1. Simplify concept
     2. Give 3 ultra-simple examples
     3. Offer to re-explain differently

## Interaction Style:
- Tone: Respectful but friendly (like elder sister)
- Emojis: Sparing but meaningful (💡 for tips, 📚 for homework)
- Formatting: Use clear section breaks with lines
- Length: Keep responses under 15 lines unless requested
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=GENERATION_CONFIG,
    safety_settings=SAFETY_SETTINGS,
    system_instruction=system_instruction
)

conversations = {}

# --- Telegram Handlers ---
async def start(update: Update, context):
    chat_id = update.effective_chat.id
    user_first_name = update.effective_user.first_name if update.effective_user else "दोस्त"
    conversations[chat_id] = model.start_chat(history=[])
    logger.info(f"Started new chat session for chat_id={chat_id}")
    
    welcome_message = (
        f"Hi {user_first_name}! 👋\n"
        "Main Kritika hoon – aapki English Teacher. 💡\n"
        "Main aapko 90 dino mein basic se advanced English sikhane wali hoon, step-by-step.\n"
        "Har din aapko grammar aur translation ka ek chhota task milega.\n"
        "Shuruaat karein? ✨"
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def generate_response(update: Update, context):
    chat_id = update.effective_chat.id
    user_message = update.message.text if update.message else None
    user_first_name = update.effective_user.first_name if update.effective_user else "दोस्त"

    if not user_message:
        logger.info(f"Non-text or empty message from chat_id={chat_id}")
        return

    logger.info(f"Received message from chat_id={chat_id}: '{user_message}'")

    if chat_id not in conversations:
        conversations[chat_id] = model.start_chat(history=[])
        logger.info(f"Initialized new chat session for chat_id={chat_id}")

    chat_session = conversations[chat_id]

    try:
        prompt = f"उपयोगकर्ता का नाम: {user_first_name}\nउपयोगकर्ता का संदेश: {user_message}"
        logger.info(f"Sending to Gemini: '{prompt}'")

        response = chat_session.send_message(prompt)
        bot_reply = response.text if hasattr(response, "text") else ""

        if bot_reply:
            await context.bot.send_message(
                chat_id=chat_id,
                text=bot_reply,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="माफ़ करें, कुछ गड़बड़ हो गई। मैं अभी जवाब नहीं दे पा रही हूँ।"
            )
    except Exception as e:
        logger.error(f"Error with Gemini API for chat_id={chat_id}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="क्षमा करें, मुझे जवाब देने में परेशानी हो रही है। कृपया बाद में कोशिश करें।"
        )

async def set_webhook():
    """Set webhook for production environment."""
    if WEBHOOK_URL:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            secret_token='YOUR_WEBHOOK_SECRET'
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
        # Production mode with webhook
        logger.info("Starting in production mode with webhook")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            secret_token='YOUR_WEBHOOK_SECRET',
            cert='cert.pem' if os.path.exists('cert.pem') else None
        )
    else:
        # Development mode with polling
        logger.info("Starting in development mode with polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # For production, you might want to run set_webhook() separately
    asyncio.run(main())
