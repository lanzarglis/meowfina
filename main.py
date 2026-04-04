python
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем токены из переменных окружения
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

# URL для OpenRouter API
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Модель по умолчанию
DEFAULT_MODEL = "openai/gpt-3.5-turbo"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Meowfina — бот-переводчик с кошачьего на человеческий 🐱\n\nНапиши мне что-нибудь, и я переведу!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я перевожу с кошачьего языка на человеческий!\nПросто напиши мне кошачьи звуки или фразы 🐱")

async def translate_to_human(text: str) -> str:
    """Перевод с кошачьего на человеческий через OpenRouter"""
    if not OPENROUTER_API_KEY:
        return "Ошибка: API ключ не настроен. Настрой OPENROUTER_API_KEY в Railway."
    
    prompt = f"""Ты — Meowfina, мудрый кот-оракул. Переведи следующий кошачий текст на человеческий язык.
Добавь немного мудрости и кошачьего шарма.

Кошачий текст: {text}

Перевод:"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://meowfina.railway.app",
        "X-Title": "Meowfina"
    }
    
    data = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"OpenRouter error: {result}")
            return "Не удалось перевести. Попробуй еще раз!"
    except Exception as e:
        logger.error(f"Request error: {e}")
        return f"Ошибка: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Переводим текст
    translation = await translate_to_human(user_text)
    
    await update.message.reply_text(translation)

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден!")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Обработчик сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Meowfina запущена!")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()
