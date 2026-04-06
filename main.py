import os
import logging
import tempfile
import subprocess
import speech_recognition as sr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# DEEP SCIENTIFIC CAT DICTIONARY
CAT_DICT = {
    'мяу': '🐱 МЯУКАНИЕ\n━━━━━━━━━━━━━━━━\nЧастота: 1-4 кГц\nЗначение: Приветствие или просьба\nКонтекст: Голод или внимание?\n\n🔬 Научное: Коты "разговаривают" с людьми!',
    'мяу-мяу': '🐱 МЯУ-МЯУ\n━━━━━━━━━━━━━━━━\nЧастота: 2-4 кГц\nЗначение: Настоятельная просьба (ЕДА)\n\n🔬 Научное: Высокий питч = сильная потребность',
    'мяууу': '🐱 МЯУУУ\n━━━━━━━━━━━━━━━━\nЧастота: 3-5 кГц\nЗначение: Жалоба, сильная потребность\n\n🔬 Научное: Длинный звук = дискомфорт',
    'мяу!': '🐱 МЯУ!\n━━━━━━━━━━━━━━━━\nЧастота: 4-6 кГц\nЗначение: Экстренный сигнал!\n\n🔬 Научное: Критическая частота!',
    'мур': '🐱 МУРЛЫКАНЬЕ\n━━━━━━━━━━━━━━━━\nЧастота: 25-150 Гц\nЗначение: Удовольствие или стресс\n\n🔬 Научное: 25 Hz — лечебная частота!',
    'мурр': '🐱 МУРР\n━━━━━━━━━━━━━━━━\nЧастота: 25-100 Гц\nЗначение: Глубокое расслабление\n\n🔬 Научное: Мурлыканье = лечебная частота!',
    'муррр': '🐱 МУРРР\n━━━━━━━━━━━━━━━━\nЧастота: 25-50 Гц\nЗначение: Полное блаженство\n\n🔬 Научное: Низкая частота = глубокий покой',
    'чик': '🐱 ЧИРИКАНЬЕ\n━━━━━━━━━━━━━━━━\nЧастота: 3-6 кГц\nЗначение: Охота! Вижу добычу!\n\n🔬 Научное: Возбуждение + фрустрация',
    'чирик': '🐱 ЧИРИК\n━━━━━━━━━━━━━━━━\nЧастота: 4-6 кГц\nЗначение: Азарт охотника\n\n🔬 Научное: Высокий питч = пик возбуждения',
    'щелк': '🐱 ЩЁЛК\n━━━━━━━━━━━━━━━━\nЧастота: 5-6 кГц\nЗначение: Щелчок челюстью\n\n🔬 Научное: Фрустрация: добыча недоступна',
    'трр': '🐱 ТРЕЛЬ\n━━━━━━━━━━━━━━━━\nЧастота: 0.3-3 кГц\nЗначение: Приветствие!\n\n🔬 Научное: Мама-кошка зовёт котят',
    'тррр': '🐱 ТРРР\n━━━━━━━━━━━━━━━━\nЧастота: 0.5-2 кГц\nЗначение: Тёплое приветствие\n\n🔬 Научное: Звук заботы',
    'шип': '🐱 ШИПЕНИЕ\n━━━━━━━━━━━━━━━━\nЧастота: 0.3-1.5 кГц\nЗначение: Предупреждение\n\n🔬 Научное: Инстинкт самозащиты',
    'фыр': '🐱 ФЫРКАНЬЕ\n━━━━━━━━━━━━━━━━\nЧастота: 0.5-2 кГц\nЗначение: Раздражение\n\n🔬 Научное: Мягкое предупреждение',
    'рыч': '🐱 РЫЧАНИЕ\n━━━━━━━━━━━━━━━━\nЧастота: 0.1-0.5 кГц\nЗначение: Серьёзное предупреждение\n\n🔬 Научное: Низкая частота = угроза',
    'ау': '🐱 АУ!\n━━━━━━━━━━━━━━━━\nЧастота: 4-8 кГц\nЗначение: Боль или страх\n\n🔬 Научное: Высокий питч = острая боль',
    'крик': '🐱 КРИК\n━━━━━━━━━━━━━━━━\nЧастота: 6-10 кГц\nЗначение: Сильная боль или паника\n\n🔬 Научное: Критический сигнал!',
}

def cat_translate(text):
    if not text or not text.strip():
        return '🐱 Мяу? (Не понимаю...)\n\nПопробуй мяукнуть!)'
    
    text_lower = text.lower().strip()
    found = []
    
    for cat_sound, meaning in CAT_DICT.items():
        if cat_sound in text_lower:
            found.append(meaning)
    
    if found:
        result = '🔬 ГЛУБОКИЙ НАУЧНЫЙ ПЕРЕВОД:\n\n' + '\n\n'.join(found)
        result += '\n\n📚 Источники: Animal Behaviour, акустика'
        return result
    
    en = translate(text, 'ru', 'en')
    if not en:
        return '🐱 Не распознано.\n\nКот молчит. Попробуй мяукнуть!'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return '🐱 Не распознано.\n\nКот молчит. Попробуй мяукнуть!'
    return f'🐱 Неизвестный звук.\n\nПеревод: {ru}\n\n(Это не кошачий!)'

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

def speech_to_text(audio_url):
    """Convert voice to text using SpeechRecognition (Google API)"""
    try:
        # Download audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_ogg:
            tmp_ogg_path = tmp_ogg.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_wav:
            tmp_wav_path = tmp_wav.name
        
        # Download file
        response = requests.get(audio_url)
        with open(tmp_ogg_path, 'wb') as f:
            f.write(response.content)
        
        # Convert ogg to wav using ffmpeg
        subprocess.run(['ffmpeg', '-y', '-i', tmp_ogg_path, '-ac', '1', '-ar', '16000', tmp_wav_path], 
                       capture_output=True, timeout=60)
        
        # Recognize
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_wav_path) as source:
            audio = recognizer.record(source)
        
        text = recognizer.recognize_google(audio, language='ru-RU')
        logger.info(f'Recognized: {text}')
        return text
        
    except sr.UnknownValueError:
        logger.error('Speech not recognized')
        return None
    except Exception as e:
        logger.error(f'Speech to text error: {e}')
        return None

async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text('🔬 Мяуфина v3 — БЕСПЛАТНОЕ РАСПОЗНАВАНИЕ!\n\nТеперь использую Google Speech API (бесплатно).\n\nОтправь голосовое — переведу!')

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text('🔬 Команды:\n/start — Начать\n/help — Помощь\n\nОтправь голосовое с кошачьими звуками!')

async def handle_message(update: Update, context: CallbackContext):
    translation = cat_translate(update.message.text)
    await update.message.reply_text(translation)

async def handle_voice(update: Update, context: CallbackContext):
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
        logger.info(f'Voice file URL: {file_url}')

        await update.message.reply_text('🔬 Слушаю... Распознаю...')

        text = speech_to_text(file_url)

        if text:
            translation = cat_translate(text)
            await update.message.reply_text(f'🔬 Распознано: "{text}"\n\n{translation}')
        else:
            await update.message.reply_text('🔬 Не удалось распознать. Попробуй ещё раз!')

    except Exception as e:
        logger.error(f'Voice handling error: {e}')
        await update.message.reply_text('🔬 Ошибка. Попробуй ещё!')

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error('TELEGRAM_BOT_TOKEN not set')
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info('Meowfina v3 — FREE SPEECH API!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
