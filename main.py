import os
import logging
import tempfile
import subprocess
import base64
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# CAT DICTIONARY
CAT_DICT = {
    'мур': 'Мяу! (Я соскучился/хочу внимания)',
    'мря': 'Мяу! (Голоден!)',
    'мрр': 'Мурлыканье (Я доволен)',
    'мяу': 'Стандартное приветствие',
    'хрю': 'Что-то интересное!',
    'гав': 'Осторожно!',
    'пф': 'Мне не нравится',
    'бип': 'Хочу поиграть!',
    'кря': 'Давай поиграем!',
    'муу': 'Я голоден! (Тяжёлый случай)',
    'фаа': 'Мне скучно',
    'фиу': 'Охочусь на что-то',
    'ням': 'Вкусняшка!',
    'кот': 'Кошачья конференция',
    'нек': 'Приветствие другого кота',
    'шип': 'Назад! Опасно!',
    'фрр': 'Предупреждение (сержусь)',
    'арр': 'Я тут главный!',
    'грр': 'Не трогай меня!',
    'урр': 'Я сильный и смелый!',
    'охота': 'Замечена добыча',
    'птица': 'Вижу птицу!',
    'мышь': 'Вижу мышь!',
    'муха': 'Вижу насекомое!',
    'дверь': 'Хочу выйти/войти',
    'лоток': 'Нужно в туалет',
    'вода': 'Хочу пить',
    'спать': 'Устал, хочу спать',
    'играть': 'Поиграй со мной!',
    'гладить': 'Погладь меня!',
    'мячик': 'Хочу мячик!',
    'мышка': 'Хочу мышку!',
    'коробка': 'Это моё!',
    'когтеточка': 'Точу когти',
    'смотрю': 'Наблюдаю за объектом',
    'конкурент': 'Это кто-то чужой!',
}

def cat_translate(text):
    if not text or not text.strip():
        return '🐱 Не могу распознать... (Попробуй ещё раз!)'

    text_lower = text.lower().strip()
    found = []

    for cat_sound, meaning in CAT_DICT.items():
        if cat_sound in text_lower:
            found.append(meaning)

    if found:
        result = '🐱 Перевод с кошачьего:\n\n' + '\n'.join(found)
        result += '\n\n🐾 Animal Behavios, Ltd.'
        return result

    en = translate(text, 'ru', 'en')
    if not en:
        return '🐱 Не могу перевести. Попробуй ещё раз!'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return '🐱 Не могу перевести. Попробуй ещё раз!'
    return f'🐱 Перевод:\n\n{ru}'


def translate(text, src='ru', tgt='en'):
    try:
        url = 'https://api.mymemory.translated.net/get'
        params = {'q': text, 'langpair': f'{src}|{tgt}'}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('responseStatus') == 200:
                return data.get('responseData', {}).get('translatedText', '')
        return None
    except Exception as e:
        logger.error(f'Translate exception: {e}')
        return None


async def speech_to_text(voice_url):
    """Convert voice to text using Google Speech API via HTTP"""
    try:
        logger.info(f'Downloading voice from: {voice_url}')

        # Download audio
        response = requests.get(voice_url, timeout=30)
        audio_content = response.content
        logger.info(f'Downloaded {len(audio_content)} bytes')

        # Convert ogg to wav using ffmpeg
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_ogg:
            tmp_ogg.write(audio_content)
            tmp_ogg_path = tmp_ogg.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_wav:
            tmp_wav_path = tmp_wav.name

        logger.info('Converting ogg to wav...')
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', tmp_ogg_path, '-ac', '1', '-ar', '16000', tmp_wav_path],
            capture_output=True, timeout=60
        )
        if result.returncode != 0:
            logger.error(f'ffmpeg error: {result.stderr.decode()}')
            return None

        # Read wav file
        with open(tmp_wav_path, 'rb') as f:
            audio_b64 = base64.b64encode(f.read()).decode('utf-8')

        logger.info('Calling Google Speech API...')

        # Use Google Speech-to-Text API (free tier)
        url = 'https://speech.googleapis.com/v1/speech:recognize'
        params = {'key': 'AIzaSyBOti4mN-6x-noVNwNUf2D2j1h2MGoMypQ'}

        data = {
            'config': {
                'encoding': 'LINEAR16',
                'sampleRateHertz': 16000,
                'languageCode': 'ru-RU'
            },
            'audio': {
                'content': audio_b64
            }
        }

        resp = requests.post(url, params=params, json=data, timeout=30)
        logger.info(f'Google API response: {resp.status_code}')

        if resp.status_code == 200:
            result_data = resp.json()
            if 'results' in result_data and result_data['results']:
                transcript = result_data['results'][0]['alternatives'][0]['transcript']
                logger.info(f'Recognized: {transcript}')
                return transcript

        logger.error(f'Google API error: {resp.text}')
        return None

    except Exception as e:
        logger.error(f'Speech to text error: {e}')
        return None


async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text('🐱 Meowfina v4 — Google Speech API!\n/start — начать\n/help — помощь\n\nОтправь голосовое — переведу с кошачьего!')


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text('🐱 Команды:\n/start — начать\n/help — помощь\n\nПросто отправь голосовое — я переведу!')


async def handle_message(update: Update, context: CallbackContext):
    translation = cat_translate(update.message.text)
    await update.message.reply_text(translation)


async def handle_voice(update: Update, context: CallbackContext):
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
        logger.info(f'Voice file URL: {file_url}')

        await update.message.reply_text('🐱 Распознаю голос...')

        text = await speech_to_text(file_url)

        if text:
            translation = cat_translate(text)
            await update.message.reply_text(f'🐱 Распознано: "{text}"\n\n{translation}')
        else:
            await update.message.reply_text('🐱 Не удалось распознать. Попробуй ещё раз!')
    except Exception as e:
        logger.error(f'Voice handling error: {e}')
        await update.message.reply_text('🐱 Ошибка. Попробуй ещё раз!')


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error('TELEGRAM_BOT_TOKEN not set')
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info('Meowfina v4 — Google Speech API!')
    app.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()
