import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

# URL Hugging Face Inference API
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Meowfina — переводчик с кошачьего на человеческий 🐱\n\nПросто напиши мне что-нибудь на кошачьем языке!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши мне кошачьи звуки, и я переведу их на человеческий! 🐱➡️👨")

async def translate_to_human(text: str) -> str:
    if not HF_TOKEN:
        return "Ошибка: HF_TOKEN не настроен. Добавьте переменную HF_TOKEN в Railway."
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": text,
        "parameters": {
            "src_lang": "ru_RU",
            "tgt_lang": "en_XX"
        }
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            english_text = result[0].get('translation_text', '')
            
            payload_ru = {
                "inputs": english_text,
                "parameters": {
                    "src_lang": "en_XX",
                    "tgt_lang": "ru_RU"
                }
            }
            
            response_ru = requests.post(HF_API_URL, headers=headers, json=payload_ru, timeout=30)
            result_ru = response_ru.json()
            
            if isinstance(result_ru, list) and len(result_ru) > 0:
                return result_ru[0].get('translation_text', '')
            
            return english_text
        else:
            logger.error(f"Hugging Face error: {result}")
            return "Не удалось перевести. Попробуй ещё раз!"
    except Exception as e:
        logger.error(f"Request error: {e}")
        return f"Ошибка: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    translation = await translate_to_human(user_text)
    await update.message.reply_text(translation)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Meowfina запущена!")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()