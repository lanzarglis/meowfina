python
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Мяуфина — переводчик с кошачьего на человеческий 🐱\n\nМяу!")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_text = update.message.text
    
    # Простая логика перевода (заглушка)
    translations = {
        "мяу": "привет",
        "мрр": "мурлычу",
        "гав": "пёс",
        "ня": "хочу еды"
    }
    
    result = translations.get(cat_text.lower(), f"Я не поняла: {cat_text} 🐱")
    await update.message.reply_text(result)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден!")
        return
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    
    logger.info("Мяуфина запущена!")
    app.run_polling()

if __name__ == "__main__":
    main()
