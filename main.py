python
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

CAT = {
    "мяу": "Привет!", "мур": "Люблю", "гав": "Дай поесть",
    "хрю": "На ручки", "ква": "Поиграй", "биск": "Дай воды",
    "пёс": "Уходи", "фрр": "Не трогай", "улюлю": "Погладь",
    "ням": "Вкусно!", "ззз": "Сплю", "meow": "Привет!",
    "purr": "Мурлыкаю", "hiss": "Назад!", "yawn": "Устал",
}

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    result = [CAT.get(w, w) for w in text.split()]
    if result != text.split():
        await update.message.reply_text(" → ".join(result))

app = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
app.run_polling()
