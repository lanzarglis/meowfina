import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

def translate(text, src='ru', tgt='en'):
    url = 'https://translate.googleapis.com/translate_a/single'
    params = {'client': 'gtx', 'sl': src, 'tl': tgt, 'dt': 't', 'q': text}
    try:
        resp = requests.get(url, params=params, timeout=10)
        result = resp.json()
        if result and result[0]:
            return ''.join([item[0] for item in result[0] if item[0]])
    except Exception as e:
        logger.error(f'Translate error: {e}')
        return 'Ошибка перевода'
    return 'Не удалось перевести'

def cat_translate(text):
    en = translate(text, 'ru', 'en')
    return translate(en, 'en', 'ru')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я Meowfina — переводчик 🐱')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пиши — переведу!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    translation = cat_translate(update.message.text)
    await update.message.reply_text(translation)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error('TELEGRAM_BOT_TOKEN not set')
        return
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info('Meowfina started!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()