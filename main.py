import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN', '')  # HuggingFace token (бесплатный)

# MyMemory Translate API (бесплатный)
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
    if not text or not text.strip():
        return 'Пустой текст'
    en = translate(text, 'ru', 'en')
    if not en:
        return 'Ошибка перевода'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return 'Ошибка перевода'
    return ru

# Whisper STT через HuggingFace
def speech_to_text(file_path):
    try:
        url = 'https://api-inference.huggingface.co/models/openai/whisper-small'
        headers = {'Authorization': f'Bearer {HF_TOKEN}'} if HF_TOKEN else {}
        with open(file_path, 'rb') as f:
            data = f.read()
        resp = requests.post(url, headers=headers, data=data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            return result.get('text', '')
        else:
            logger.error(f'STT error: {resp.status_code} - {resp.text}')
            return None
    except Exception as e:
        logger.error(f'STT exception: {e}')
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я Meowfina — переводчик с кошачьего 🐱\n\nПиши текстом или отправь голосовое!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пиши или отправь голосовое — переведу!')

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка голосовых сообщений"""
    await update.message.reply_text('🎤 Получил голосовое, обрабатываю...')
    
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        
        # Скачиваем файл
        ogg_path = f'/tmp/voice_{update.message.message_id}.ogg'
        await file.download_to_drive(ogg_path)
        
        # Распознаём речь
        text = speech_to_text(ogg_path)
        
        if text:
            await update.message.reply_text(f'Распознал: "{text}"')
            translation = cat_translate(text)
            await update.message.reply_text(f'Перевод: {translation}')
        else:
            await update.message.reply_text('Не удалось распознать голосовое. Попробуй ещё раз или напиши текстом!')
            
    except Exception as e:
        logger.error(f'Voice error: {e}')
        await update.message.reply_text(f'Ошибка: {str(e)[:100]}')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        await handle_voice(update, context)
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
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    logger.info('Meowfina started with voice support!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()