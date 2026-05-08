import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

load_dotenv()  # loads TELEGRAM_BOT_TOKEN from .env

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simply echoes back whatever the user sends."""
    await update.message.reply_text(f"You said: {update.message.text}")

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

print("Bot is running... press Ctrl+C to stop.")
app.run_polling()
