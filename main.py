import os
import logging
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextType

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

# Cat dictionary - real cat translations
CAT_DICT = {
    'мяу': 'я голодный / накорми меня',
    'мур': 'погладь меня / я тебя люблю',
    'мурр': 'мне хорошо / я счастлив',
    'гав': 'сторож / опасность',
    'хрю': 'привет / поиграй со мной',
    'кря': 'дай поесть',
    'шип': 'уйди / не трогай меня',
    'трель': 'я рад тебя видеть',
    'фыр': 'мне не нравится',
    'воу': 'охота / вижу добычу',
}

def cat_translate(text):
    """Translate cat sounds to human language"""
    if not text or not text.strip():
        return '🐱 Мяу? (Не понимаю...)'
    
    text_lower = text.lower()
    found = []
    
    for cat_sound, meaning in CAT_DICT.items():
        if cat_sound in text_lower:
            found.append(f"{cat_sound} → {meaning}")
    
    if found:
        return '🐱 Перевод:\n' + '\n'.join(found)
    
    # No known cat sounds - use MyMemory as fallback
    en = translate(text, 'ru', 'en')
    if not en:
        return '🐱 Не распознано. Попробуй мяукнуть!'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return '🐱 Не распознано. Попробуй мяукнуть!'
    return f'🐱 Перевод:\n{ru}'

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

def speech_to_text(audio_url):
    try:
        if not ASSEMBLYAI_API_KEY:
            logger.error('ASSEMBLYAI_API_KEY not set')
            return None

        # Transcribe audio
        transcribe_resp = requests.post(
            'https://api.assemblyai.com/v2/transcribe',
            headers={'authorization': ASSEMBLYAI_API_KEY},
            json={
                'audio_url': audio_url,
                'language_detection': True
            },
            timeout=60
        )

        if transcribe_resp.status_code != 200:
            logger.error(f'Transcribe request error: {transcribe_resp.text}')
            return None

        transcribe_id = transcribe_resp.json()['id']
        logger.info(f'Transcription ID: {transcribe_id}')

        # Poll for result
        for _ in range(20):  # Max 60 seconds
            time.sleep(3)
            result = requests.get(
                f'https://api.assemblyai.com/v2/transcription/{transcribe_id}',
                headers={'authorization': ASSEMBLYAI_API_KEY}
            )
            result_json = result.json()
            logger.info(f'Transcription status: {result_json.get("status")}')

            if result_json['status'] == 'completed':
                return result_json['text']
            elif result_json['status'] == 'error':
                logger.error(f'Transcription error: {result_json}')
                return None

        logger.error('Transcription timeout')
        return None

    except Exception as e:
        logger.error(f'Speech to text exception: {e}')
        return None

async def start_command(update: Update, context: ContextType.DEFAULT_TYPE):
    await update.message.reply_text('🐱 Привет! Я Мяуфина - кошачий переводчик!\n\nОтправь мне голосовое "мяу" - и я переведу его на человеческий язык!')

async def help_command(update: Update, context: ContextType.DEFAULT_TYPE):
    await update.message.reply_text('🐱 Команды:\n/start - Начать\n/help - Помощь\n\nПросто отправь мне голосовое сообщение с мяуканьем!')

async def handle_message(update: Update, context: ContextType.DEFAULT_TYPE):
    translation = cat_translate(update.message.text)
    await update.message.reply_text(translation)

async def handle_voice(update: Update, context: ContextType.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        # Get direct URL from Telegram
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
        logger.info(f'Voice file URL: {file_url}')

        await update.message.reply_text('🐱 Слушаю... Распознаю голос...')

        text = speech_to_text(file_url)

        if text:
            translation = cat_translate(text)
            await update.message.reply_text(f'🐱 Распознано: {text}\n\n{translation}')
        else:
            await update.message.reply_text('🐱 Не удалось распознать голос. Попробуй ещё раз!')

    except Exception as e:
        logger.error(f'Voice handling error: {e}')
        await update.message.reply_text('🐱 Ошибка при обработке голоса. Попробуй ещё раз!')

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error('TELEGRAM_BOT_TOKEN not set')
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info('Meowfina started!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
