Python
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Мяуфина — переводчик с кошачьего 🐱\nНапиши мне что-нибудь!")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_text = update.message.text

    translations = {
        "мяу": "привет",
        "мрр": "мурлычу",
        "гав": "пёс",
        "ня": "хочу еды",
        "ффрр": "злая",
        "хрр": "сплю"
    }
    
    result = translations.get(cat_text.lower(), f"Не поняла: {cat_text} 🐱")
    await update.message.reply_text(result)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан")
        return

    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    
    logger.info("Бот Мяуфина запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
