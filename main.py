import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# MyMemory Translate API (бесплатный, без ключа)
def translate(text, src='ru', tgt='en'):
    try:
        url = 'https://api.mymemory.translated.net/get'
        params = {'q': text, 'langpair': f'{src}|{tgt}'}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('responseStatus') == 200:
                return data.get('responseData', {}).get('translatedText', '')
        logger.error(f'Translate error: {resp.text}')
        return None
    except Exception as e:
        logger.error(f'Translate exception: {e}')
        return None

def cat_translate(text):
    # Russian -> English -> Russian (двойной перевод для "кошачьего" эффекта)
    en = translate(text, 'ru', 'en')
    if not en:
        return 'Ошибка перевода'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return 'Ошибка перевода'
    return ru

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я Meowfina — переводчик 🐱')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пиши или отправь голосовое — переведу!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        await update.message.reply_text('Голосовые пока не поддерживаются. Напиши текстом!')
        return
    
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
    app.add_handler(MessageHandler(filters.VOICE, handle_message))
    
    logger.info('Meowfina started!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()