"""Telegram adapter that reuses the shared construction-agent pipeline."""

import os
import sys

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from channels.base import Channel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from memory import log_message
from pipeline import process_incoming_message


class TelegramChannel(Channel):
    """Telegram Bot API adapter for construction communication demos."""

    channel_name = "telegram"

    def __init__(self):
        load_dotenv()
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not self._token:
            raise RuntimeError(
                "Missing TELEGRAM_BOT_TOKEN in .env. "
                "Create a bot with BotFather and add the token."
            )
        self._app = None
        self._message_count = 0

    def fetch_messages(self) -> list[dict]:
        """Telegram is event-driven, so polling callbacks handle messages."""
        return []

    def send_message(
        self,
        recipient: str,
        text: str,
        subject: str = "",
        dry_run: bool = False,
    ) -> bool:
        del subject
        if dry_run:
            print(f"[telegram] DRY RUN -> {recipient}: {text[:80]}")
            return True
        return False

    def run(self):
        self._app = ApplicationBuilder().token(self._token).build()
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("status", self._cmd_status))
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

        print("=" * 50)
        print("CEM501 Agent Bot - Telegram Channel")
        print("=" * 50)
        print("Bot is running... press Ctrl+C to stop.")
        print()

        self._app.run_polling()

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        del context
        await update.message.reply_text(
            "CEM501 Construction Agent Bot\n\n"
            "Send a construction project message and I will classify it, "
            "log it to memory, and draft a response."
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        del context
        await update.message.reply_text(
            "Supported construction categories:\n"
            "- RFI\n"
            "- Delay\n"
            "- Approval\n"
            "- Site Issue\n"
            "- Safety\n"
            "- Procurement\n"
            "- Progress / Report"
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        del context
        await update.message.reply_text(
            f"Session Stats\nMessages processed: {self._message_count}"
        )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        del context
        incoming_text = update.message.text
        sender_name = update.message.from_user.full_name or update.message.from_user.first_name or "User"
        chat_id = str(update.effective_chat.id)

        result = process_incoming_message(
            {
                "sender": sender_name,
                "sender_phone": chat_id,
                "subject": "Telegram message",
                "text": incoming_text,
                "channel": self.channel_name,
            },
            send_reply=False,
        )

        classification = result["classification"]
        response = (
            f"Category: {classification['category']}\n"
            f"Type: {classification['message_type']}\n"
            f"Matched keyword: {classification['matched_keyword']}\n\n"
            f"Draft response:\n{result['draft']}"
        )

        await update.message.reply_text(response)
        log_message(
            contact_id=result["contact_id"],
            direction="sent",
            subject="Telegram draft response",
            body=result["draft"],
            channel=self.channel_name,
        )

        self._message_count += 1
        print(
            f"[telegram] {sender_name} -> {classification['category']} / "
            f"{classification['message_type']} (keyword: {classification['matched_keyword']})"
        )
