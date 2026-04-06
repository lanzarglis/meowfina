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

# Scientific cat dictionary - based on Animal Behaviour research
CAT_DICT = {
    # Meowing - different types for different needs
    'мяу': 'Мяуканье (通用) — приветствие, голод или просьба внимания',
    'мяу-мяу': 'Мяу-мяу — настоятельная просьба (чаще всего еда)',
    'мяууу': 'Мяууу — долгий жалобный звук — сильная потребность',
    
    # Purring - can mean contentment OR stress/pain
    'мур': 'Мурлыканье — удовольствие и комфорт (НО: может означать стресс!)',
    'мурр': 'Мурр — глубокое мурлыканье — расслабление',
    'муррр': 'Муррр — очень довольный кот',
    
    # Chirping/Chattering - hunting excitement + frustration
    'чик': 'Чириканье — вижу добычу! Охота началась',
    'чирик': 'Чирик — возбуждение от потенциальной жертвы',
    'щелк': 'Щелк челюстью — фрустрация: не могу достать добычу',
    
    # Trilling - greeting, affection
    'трр': 'Трель — приветствие! Рад тебя видеть',
    'тррр': 'Тррр — мягкое приветствие от мамы-кошки к котятам',
    
    # Growling/Hissing - warnings
    'шип': 'Шипение — предупреждение: уйди, не приближайся!',
    'фыр': 'Фырканье — раздражение, мне не нравится',
    'рыч': 'Рычание — сильное предупреждение, готов к атаке',
    'гав': 'Гав — редко, но бывает: защита территории',
    
    # Screeching/shrieks - pain or extreme distress
    'ау': 'Ау! — боль или внезапный страх',
    'крик': 'Крик — сильная боль или паника',
}

def cat_translate(text):
    """Translate cat sounds to human language - scientific approach"""
    if not text or not text.strip():
        return '🐱 Мяу? (Не понимаю...)\n\nПопробуй мяукнуть!)'
    
    text_lower = text.lower().strip()
    found = []
    
    # Check exact matches first
    for cat_sound, meaning in CAT_DICT.items():
        if cat_sound in text_lower:
            found.append(f"🐾 '{cat_sound}' → {meaning}")
    
    if found:
        result = '🐱 Перевод с кошачьего (научный):\n\n' + '\n\n'.join(found)
        result += '\n\n📚 Источник: исследования Animal Behaviour'
        return result
    
    # No known cat sounds - use MyMemory as fallback
    en = translate(text, 'ru', 'en')
    if not en:
        return '🐱 Не распознано.\n\nКот молчит или издаёт неизвестный звук. Попробуй мяукнуть!'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return '🐱 Не распознано.\n\nКот молчит или издаёт неизвестный звук. Попробуй мяукнуть!'
    return f'🐱 Неизвестный звук.\n\nПеревод: {ru}\n\n(Это не кошачий — попробуй мяу!)'

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
    await update.message.reply_text('🐱 Привет! Я Мяуфина — кошачий переводчик!\n\nМоя логика основана на научных исследованиях вокализации кошек (Animal Behaviour).\n\nОтправь мне голосовое с мяуканьем — и я переведу!')

async def help_command(update: Update, context: ContextType.DEFAULT_TYPE):
    await update.message.reply_text('🐱 Команды:\n/start — Начать\n/help — Помощь\n\nПросто отправь мне голосовое сообщение с кошачьими звуками!')

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
            await update.message.reply_text(f'🐱 Распознано: "{text}"\n\n{translation}')
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

    logger.info('Meowfina started with scientific dictionary!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
