import os
import logging
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

# DEEP SCIENTIFIC CAT DICTIONARY
# Based on research: Animal Behaviour, acoustic analysis (300-6000 Hz)
CAT_DICT = {
    # === МЯУКАНИЕ (Meowing) ===
    'мяу': '🐱 МЯУКАНИЕ\n━━━━━━━━━━━━━━━━\nЧастота: 1-4 кГц\nЗначение: Приветствие или просьба\nКонтекст: Проверь — голод или внимание?\n\n🔬 Научное: Коты "разговаривают" с людьми!',
    
    'мяу-мяу': '🐱 МЯУ-МЯУ\n━━━━━━━━━━━━━━━━\nЧастота: 2-4 кГц (повышенная)\nЗначение: Настоятельная просьба\nКонтекст: Скорее всего, ЕДА.\n\n🔬 Научное: Высокий питч = сильная потребность',
    
    'мяууу': '🐱 МЯУУУ\n━━━━━━━━━━━━━━━━\nЧастота: 3-5 кГц (высокая)\nЗначение: Жалоба, сильная потребность\nКонтекст: Голод или одиночество.\n\n🔬 Научное: Длинный звук = дискомфорт',
    
    'мяу!': '🐱 МЯУ!\n━━━━━━━━━━━━━━━━\nЧастота: 4-6 кГц (максимальная)\nЗначение: Экстренный сигнал!\nКонтекст: Боль, страх или немедленная нужда.\n\n🔬 Научное: Критическая частота — реагируй!',
    
    # === МУРЛЫКАНЬЕ (Purring) ===
    'мур': '🐱 МУРЛЫКАНЬЕ\n━━━━━━━━━━━━━━━━\nЧастота: 25-150 Гц\nЗначение: Удовольствие или стресс\nКонтекст: Смотри на тело кота!\n\n🔬 Научное: 25 Гц — частота вибрации костей/заживления',
    
    'мурр': '🐱 МУРР\n━━━━━━━━━━━━━━━━\nЧастота: 25-100 Гц\nЗначение: Глубокое расслабление\nКонтекст: Кот счастлив и спокоен.\n\n🔬 Научное: Мурлыканье = 25-150 Hz = лечебная частота!',
    
    'муррр': '🐱 МУРРР\n━━━━━━━━━━━━━━━━\nЧастота: 25-50 Гц (очень низкая)\nЗначение: Полное блаженство\nКонтекст: Максимальное доверие.\n\n🔬 Научное: Низкая частота = глубокий покой',
    
    # === ЧИРИКАНЬЕ (Chirping) ===
    'чик': '🐱 ЧИРИКАНЬЕ\n━━━━━━━━━━━━━━━━\nЧастота: 3-6 кГц (высокая)\nЗначение: Охота! Вижу добычу!\nКонтекст: Смотрит на птицу/мышь.\n\n🔬 Научное: Возбуждение + фрустрация',
    
    'чирик': '🐱 ЧИРИК\n━━━━━━━━━━━━━━━━\nЧастота: 4-6 кГц\nЗначение: Азарт охотника\nКонтекст: Готов к прыжку!\n\n🔬 Научное: Высокий питч = пик возбуждения',
    
    'щелк': '🐱 ЩЁЛК\n━━━━━━━━━━━━━━━━\nЧастота: 5-6 кГц\nЗначение: Щелчок челюстью\nКонтекст: Фрустрация: добыча недоступна.\n\n🔬 Научное: Характерный звук разочарования',
    
    # === ТРЕЛЬ (Trilling) ===
    'трр': '🐱 ТРЕЛЬ\n━━━━━━━━━━━━━━━━\nЧастота: 0.3-3 кГц\nЗначение: Приветствие!\nКонтекст: Рад тебя видеть!\n\n🔬 Научное: Мама-кошка зовёт котят',
    
    'тррр': '🐱 ТРРР\n━━━━━━━━━━━━━━━━\nЧастота: 0.5-2 кГц\nЗначение: Тёплое приветствие\nКонтекст: Максимальная нежность.\n\n🔬 Научное: Звук заботы и привязанности',
    
    # === ШИПЕНИЕ (Hissing) ===
    'шип': '🐱 ШИПЕНИЕ\n━━━━━━━━━━━━━━━━\nЧастота: 0.3-1.5 кГц\nЗначение: Предупреждение\nКонтекст: Уйди! Не приближайся!\n\n🔬 Научное: Инстинкт самозащиты',
    
    'фыр': '🐱 ФЫРКАНЬЕ\n━━━━━━━━━━━━━━━━\nЧастота: 0.5-2 кГц\nЗначение: Раздражение\nКонтекст: Не нравится что-то.\n\n🔬 Научное: Мягкое предупреждение',
    
    'рыч': '🐱 РЫЧАНИЕ\n━━━━━━━━━━━━━━━━\nЧастота: 0.1-0.5 кГц (низкая)\nЗначение: Серьёзное предупреждение\nКонтекст: Готов к атаке! Отступи.\n\n🔬 Научное: Низкая частота = угроза',
    
    'гав': '🐱 ГАВ\n━━━━━━━━━━━━━━━━\nЗначение: Редкий звук\nКонтекст: Защита территории.\n\n🔬 Научное: Не типично для котов',
    
    # === КРИКИ (Screeching) ===
    'ау': '🐱 АУ!\n━━━━━━━━━━━━━━━━\nЧастота: 4-8 кГц\nЗначение: Боль или внезапный страх\nКонтекст: Что-то пошло не так.\n\n🔬 Научное: Высокий питч = острая боль',
    
    'крик': '🐱 КРИК\n━━━━━━━━━━━━━━━━\nЧастота: 6-10 кГц (максимальная)\nЗначение: Сильная боль или паника\nКонтекст: Немедленная помощь нужна!\n\n🔬 Научное: Критический сигнал!',
}

def cat_translate(text):
    """Deep scientific cat translation"""
    if not text or not text.strip():
        return '🐱 Мяу? (Не понимаю...)\n\nПопробуй мяукнуть!)'
    
    text_lower = text.lower().strip()
    found = []
    
    for cat_sound, meaning in CAT_DICT.items():
        if cat_sound in text_lower:
            found.append(meaning)
    
    if found:
        result = '🔬 ГЛУБОКИЙ НАУЧНЫЙ ПЕРЕВОД:\n\n' + '\n\n'.join(found)
        result += '\n\n📚 Источники: Animal Behaviour, акустический анализ'
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

        for _ in range(20):
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

async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text('🔬 Мяуфина v2 — ГЛУБОКИЙ НАУЧНЫЙ ПЕРЕВОД!\n\nМоя логика основана на:\n• Исследованиях Animal Behaviour\n• Акустическом анализе 300-10000 Hz\n• Частотах мурлыканья 25-150 Hz (лечебная!)\n\nОтправь голосовое — переведу с научной точностью!')

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

        await update.message.reply_text('🔬 Анализирую акустику...')

        text = speech_to_text(file_url)

        if text:
            translation = cat_translate(text)
            await update.message.reply_text(f'🔬 Распознано: "{text}"\n\n{translation}')
        else:
            await update.message.reply_text('🔬 Не удалось распознать. Попробуй ещё!')

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

    logger.info('Meowfina v2 — DEEP SCIENTIFIC MODE!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
