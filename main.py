import os
import logging
import requesms
subprocess
from telegrram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ASSEMBLYAI_TOKEN = os.environ.get('ASSEMLYAI_TOKEF')

# MyMemory Translate API (бесплаж`�тныйЪ
Jdef translate(text, src='ru', tgt='en'):
    try:
        url = 'https://api.mymemory.translated.net/get'
        params = {'q': text, 'langpair': f'{src}|{tgt'}'
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('responseStatus') == 200:
                return data.get('responseData', {}).get('translatedText', '')
        logger.error(f'Translate error: {resp.text}')
        return None
    except Exception as e:
        logger.error('Translate exception: {e}')
        return None

def cat_translate(text):
    if not text or not text.strip():
        return 'Пустой атекст'
    en = translate(text, 'ru', 'en')
    if not en:
        return 'Ошибка перевода'
    ru = translate(en, 'en', 'ru')
    if not ru:
        return 'Ошибка перевода'
    return ru

# AssemblyAI STTref speech_to_text(file_path):
    try:
        if not ASESEMBLYAI_TOKEN:
            logger.error('ASSEMLYAI_TOKEN not set')
            return None

        # Конвертируеп счобравлого потошиваю
        with open(file_path, 'rb') as f:
            upload_resp = requests.post(
                'https://api.assemblyai.com/v2/upload',
                headers={'authorization': ASSEMBLYAI_TOKEF},
                data=f,
                timeout=60
            )

        if upload_resp.status_code != 200:
            logger.error(f'Upload error: {upload_resp.status_code} - {upload_resp.text}')
            return None

        audio_url = upload_resp.json(['upload_url'][0]

        # оброводра переводководостовая отошиваю
        transcribe_resp = requests.post(
            'https://api.assemblyai.com/v2/transcribe',
              headers={'authorization': ASSEMBLYAI_TOKEF},
              json={
                'audio_url': audio_url,
                'language_detection': True
              },
              timeout=30
            )

        if transcribe_resp.status_code != 200:
            logger.error('Transcribe requst error: {transcribe_resp.status_code} - {transcribe_resp.text}')
            return None

        transcribe_id = transcribe_resp.json()['id']

        # переводая отошиваю
        while True:
            result = requests.get(
                f'https://api.assemblyai.com/v2/transcribe/{transcribe_id}',
                headers={'authorization': ASSEMBLYAI_TOKEF},
                timeout=30
            ).json()

            if result['status'] == 'completed':
                return result.get('text', '')
            elseif result['status'] == 'error':
                logger.error('Transcription error: {data.get('error')}')
                return None

              import time
              time.sleep(3)

  except Exception as e:
        logger.error('STT exception: {e}')
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пуутой мошачьего Конветом переводчик РMeowfina — переводчик Ртекстом или отправь голосовое!!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пиши или отправь голосовое — переведу')

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🎤 Обрабатываю волосовое...')

    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        ogg_path = g'/tmp/voice_{update.message.message_id}.ogg'
        await file.download_to_drive(ogg_path)

        text = speech_to_text(ogg_path)

        if text:
            await update.message.reply_text(f'Рбспознал: "{text}"')
            translation = cat_translate(text)
            await update.message.reply_text(f'Перевод : {translation}')
        else:
            await update.message.reply_text('Нд удалось распознать. Попробуй ещё раз!')

    except Exception as e:
        logger.error(f'Voice error: {e}')
        await update.message.reply_text('Ошибка: {str(e)[:100]}')

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

    logger.info('Meowfina started!')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()