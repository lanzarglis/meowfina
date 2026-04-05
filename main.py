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

# HuggingFace Inference API - НОВЫЙ формат с router.huggingface.co
MODEL_ID = "Helsinki-NLP/opus-mt-ru-en"
HF_API_URL = f"https://router.huggingface.co/pipeline/translation/{MODEL_ID}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Meowfina — переводчик с кошачьего на человеческий 🐱\n\nПросто напиши мне что-нибудь!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши мне текст, и я переведу его! 🐱➡️👨")

async def translate_to_human(text: str) -> str:
    if not HF_TOKEN:
        return "Ошибка: HF_TOKEN не настроен. Добавьте переменную HF_TOKEN в Railway."
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": text
    }
    
    try:
        logger.info(f"Sending request to HF API: {HF_API_URL}")
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text[:500]}")
        
        if response.status_code != 200:
            return f"Ошибка API: статус {response.status_code}. Ответ: {response.text[:200]}"
        
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            english_text = result[0].get('translation_text', '')
            
            # Обратный перевод на русский
            payload_ru = {
                "inputs": english_text
            }
            
            response_ru = requests.post(
                "https://router.huggingface.co/pipeline/translation/Helsinki-NLP/opus-mt-en-ru", 
                headers=headers, json=payload_ru, timeout=60
            )
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
    
    logger.info(f"HF_TOKEN set: {bool(HF_TOKEN)}")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Meowfina запущена!")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()