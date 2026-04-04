
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Мяу! Получил: {update.message.text}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Я Meowfina — бот-переводчик с кошачьего на человеческий. мяу 🐱"
    )

if __name__ == '__main__':
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN not found!")
        exit(1)
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(CommandHandler("start", start))
    
    app.run_polling()
